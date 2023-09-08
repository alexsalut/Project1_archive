import pandas as pd
import time
import xlwings as xw

from utils import get_next_trading_day, retry_save_excel


class MonitorUpdater:
    def __init__(self, today=None):
        # self.monitor_dir = r'C:\Users\Yz02\Desktop\strategy_update_copy'
        # self.remote_monitor_dir = r'C:\Users\Yz02\Desktop\strategy_update_remote'
        self.monitor_dir = r'C:\Users\Yz02\Desktop\strategy_update'
        self.remote_monitor_dir = r'\\192.168.1.116\target_position\monitor'
        self.today = time.strftime('%Y%m%d') if today is None else today
        self.monitor_path = rf'{self.monitor_dir}/monitor_{self.today}.xlsx'
        self.remote_summary_dir = r'\\192.168.1.116\target_position\summary'
        self.next_trading_day = get_next_trading_day(self.today)

    def update_monitor(self):
        self.update_monitor_next_trading_day()
        self.archive_monitor_today()

    def archive_monitor_today(self):
        try:
            df = self.get_refreshed_data()
            df.index = df.index + 1
            df.columns = [chr(ord('A') + i) for i in range(len(df.columns))]
            app = xw.App(visible=False, add_book=False)
            wb = xw.books.open(self.monitor_path)
            sheet = wb.sheets['monitor目标持仓']
            for index in df.index:
                for col in df.columns:
                    sheet.range(f'{col}{index}').value = df.loc[index, col]

            retry_save_excel(wb=wb, file_path=self.monitor_path)
            remote_path = rf'{self.remote_monitor_dir}/monitor_{self.today}.xlsx'
            retry_save_excel(wb=wb, file_path=remote_path)
            wb.close()
            app.quit()
            print('Archive today monitor successfully')
        except Exception as e:
            print(e)
            print('Retry archive today monitor in 20 seconds')
            time.sleep(20)
            self.archive_monitor_today()

    def get_refreshed_data(self):
        df = pd.read_excel(self.monitor_path, sheet_name=0, index_col=None, header=None)
        if (df == 'Refreshing').any().any():
            print('Monitor data is refreshing, wait for 10 seconds to retry for archiving')
            self.get_refreshed_data()
        else:
            print('Monitor data refreshed and ready to be archived')
            return df

    def update_monitor_next_trading_day(self):
        try:
            app = xw.App(visible=False, add_book=False)
            app.display_alerts = False
            app.screen_updating = False
            wb = app.books.open(self.monitor_path)
            sheet = wb.sheets[0]

            sheet['B1'].value = self.next_trading_day
            stock_shares_df, tag_pos_df = self.renew_stock_list()
            for index in tag_pos_df.index:
                sheet[f'B{index + 4}'].value = tag_pos_df.loc[index, 'index']
            for index in stock_shares_df.index:
                sheet[f'A{index + 57}'].value = stock_shares_df.loc[index, 'index']
                sheet[f'B{index + 57}'].formula = f'=EM_S_INFO_NAME(A{index + 57})'
                sheet[f'C{index + 57}'].value = stock_shares_df.loc[index, '0']
                sheet[f'D{index + 57}'].formula = f'=EM_S_INFO_INDUSTRY_SW2021(A{index + 57},"1")'
                sheet[f'E{index + 57}'].formula = f'=EM_S_FREELIQCI_VALUE(A{index + 57},B1,100000000)'
                sheet[f'F{index + 57}'].formula = f'=EM_S_VAL_MV2(A{index + 57},B1,100000000)'
                sheet[f'G{index + 57}'].formula = f'=RTD("em.rtq",,A{index + 57},"Time")'
                sheet[f'H{index + 57}'].formula = f'=RTD("em.rtq",,A{index + 57},"DifferRange")'

            local_path = rf'{self.monitor_dir}/monitor_{self.next_trading_day}.xlsx'
            retry_save_excel(wb=wb, file_path=local_path)

            remote_path = rf'{self.remote_monitor_dir}/monitor_{self.next_trading_day}.xlsx'
            retry_save_excel(wb=wb, file_path=remote_path)
            wb.close()
            app.quit()
            print('Updating next trading day monitor successfully')

        except Exception as e:
            print(e)
            print('Updating next trading day monitor failed, retry in 20 seconds')
            time.sleep(20)
            self.update_monitor_next_trading_day()

    def renew_stock_list(self):
        try:
            stock_shares_df = pd.read_csv(
                rf'{self.remote_summary_dir}/stock_shares_{self.today}.csv', index_col=0,
            ).reset_index(drop=False)
            tag_pos_df = pd.read_csv(
                rf'{self.remote_summary_dir}/tag_pos_{self.today}.csv', index_col=0,
            ).reset_index(drop=False)
            empty_rows = pd.DataFrame(index=range(len(stock_shares_df), 50), columns=stock_shares_df.columns)
            stock_shares_df = pd.concat([stock_shares_df, empty_rows], axis=0)
            print('Get next trading day monitor stock list successfully')
            return stock_shares_df, tag_pos_df
        except Exception as e:
            print(e)
            print('Getting next trading day monitor stock list failed, retry in 20 seconds')
            time.sleep(20)
            self.renew_stock_list()

if __name__ == '__main__':
    MonitorUpdater('20230908').archive_monitor_today()
