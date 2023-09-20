import time
import datetime

import pandas as pd
import xlwings as xw

from utils import retry_save_excel, retry_remove_excel, send_email
from trading_calendar import TradingCalendar as tc


class StrategyMonitor:
    def __init__(self, today=None):
        # self.monitor_dir = r'C:\Users\Yz02\Desktop\strategy_update - 副本'
        # self.remote_monitor_dir = r'C:\Users\Yz02\Desktop\strategy_update - 副本 - 副本'
        self.monitor_dir = r'C:\Users\Yz02\Desktop\strategy_update'
        self.remote_monitor_dir = r'\\192.168.1.116\target_position\monitor'
        self.today = time.strftime('%Y%m%d') if today is None else today
        self.monitor_path = rf'{self.monitor_dir}/monitor_{self.today}_formula.xlsx'
        self.remote_summary_dir = r'\\192.168.1.116\target_position\summary'
        self.next_trading_day = tc().get_n_trading_day(self.today, 1).strftime('%Y%m%d')

    def update_monitor(self):
        self.update_monitor_next_trading_day()
        self.archive_monitor_today()

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

            rows_to_delete = range(57 + len(stock_shares_df), 107)
            for row in rows_to_delete:
                sheet.api.Rows(row).Delete()

            local_path = rf'{self.monitor_dir}/monitor_{self.next_trading_day}_formula.xlsx'
            retry_save_excel(wb=wb, file_path=local_path)

            remote_path = rf'{self.remote_monitor_dir}/monitor_{self.next_trading_day}_formula.xlsx'
            retry_save_excel(wb=wb, file_path=remote_path)
            wb.close()
            app.quit()
            print('[Monitor Next trading day update]Updated successfully')
            send_email(
                subject=f'Monitor next trading day updated, archive today monitor now',
                content='',
                receiver='zhou.sy@yz-fund.com.cn'
            )

        except Exception as e:
            print(e)
            print('[Monitor Next trading day update]Update failed, retry in 10 seconds')
            time.sleep(10)
            self.update_monitor_next_trading_day()

    def archive_monitor_today(self):
        try:
            df = self.get_refreshed_data()
            df.index = df.index + 1
            df = df.applymap(lambda x: str(x) if isinstance(x, datetime.time) else x)
            df.columns = [chr(ord('A') + i) for i in range(len(df.columns))]
            app = xw.App(visible=False, add_book=False)
            wb = xw.books.open(self.monitor_path)
            sheet = wb.sheets['monitor目标持仓']

            for index in df.index:
                for col in df.columns:
                    sheet.range(f'{col}{index}').value = df.loc[index, col]

            retry_save_excel(wb=wb, file_path=rf'{self.monitor_dir}/monitor_{self.today}.xlsx')
            retry_save_excel(wb=wb, file_path=rf'{self.remote_monitor_dir}/monitor_{self.today}.xlsx')

            retry_remove_excel(file_path=self.monitor_path)
            retry_remove_excel(file_path=rf'{self.remote_monitor_dir}/monitor_{self.today}_formula.xlsx')
            wb.close()
            app.quit()
            print('Archive today monitor successfully')
        except Exception as e:
            print(e)
            print('Retry archive today monitor in 10 seconds')
            time.sleep(10)
            self.archive_monitor_today()

    def get_refreshed_data(self):
        df = pd.read_excel(self.monitor_path, sheet_name=0, index_col=None, header=None)
        if (df == 'Refreshing').any().any():
            print('Monitor data is refreshing, wait for 10 seconds to retry for archiving')
            self.get_refreshed_data()
        else:
            print('Monitor data refreshed and ready to be archived')
            return df

    def renew_stock_list(self):
        try:
            stock_shares_df = pd.read_csv(
                rf'{self.remote_summary_dir}/stock_shares_{self.today}.csv', index_col=0,
            ).reset_index(drop=False)
            tag_pos_df = pd.read_csv(
                rf'{self.remote_summary_dir}/tag_pos_{self.today}.csv', index_col=0,
            ).reset_index(drop=False)
            print('[Next trading day stock list] Updated successfully')
            return stock_shares_df, tag_pos_df
        except Exception as e:
            print(e)
            print('[Next trading day stock list]Update failed, retry in 20 seconds')
            time.sleep(20)
            self.renew_stock_list()


