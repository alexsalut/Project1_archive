import time
import datetime

import xlwings as xw
import pandas as pd

from util.send_email import Mail, R
from util.utils import retry_save_excel
from util.trading_calendar import TradingCalendar
from file_location import FileLocation as FL


class CnnDailyRecord:
    def __init__(self):
        self.monitor_dir = FL.remote_monitor_dir
        self.summary_dir = FL.remote_summary_dir

    def update_monitor(self, today=None):
        today = time.strftime('%Y%m%d') if today is None else today
        self.update_monitor_next_trading_day(today)
        self.archive_monitor_today(today)

    def update_monitor_next_trading_day(self, today):

        next_trading_day = TradingCalendar().get_n_trading_day(today, 1).strftime('%Y%m%d')
        try:
            app = xw.App(visible=True, add_book=False)
            print('Generate pid:', app.pid)
            app.display_alerts = True
            app.screen_updating = True
            monitor_path = f'{self.monitor_dir}/monitor_{today}_formula.xlsx'
            wb = app.books.open(monitor_path)

            stock_shares_df, tag_pos_df = self.renew_stock_list(today)
            sheet = wb.sheets[0]
            # tag_pos_df第一行在表格中的行数
            row1 = 5
            # stock_shares_df第一行在表格中的行数
            row2 = 4 + len(tag_pos_df) + 4

            sheet['B1'].value = next_trading_day
            for index in tag_pos_df.index:
                sheet[f'B{index + row1}'].value = tag_pos_df.loc[index, 'index']
            for index in stock_shares_df.index:
                sheet[f'A{index + row2}'].value = stock_shares_df.loc[index, 'index']
                sheet[f'B{index + row2}'].formula = f'=EM_S_INFO_NAME(A{index + row2})'
                sheet[f'C{index + row2}'].value = stock_shares_df.loc[index, '0']
                sheet[f'D{index + row2}'].formula = f'=EM_S_INFO_INDUSTRY_SW2021(A{index + row2},"1")'
                sheet[f'E{index + row2}'].formula = f'=EM_S_FREELIQCI_VALUE(A{index + row2},B1,100000000)'
                sheet[f'F{index + row2}'].formula = f'=EM_S_VAL_MV2(A{index + row2},B1,100000000)'
                sheet[f'G{index + row2}'].formula = f'=RTD("em.rtq",,A{index + row2},"Time")'
                sheet[f'H{index + row2}'].formula = f'=RTD("em.rtq",,A{index + row2},"DifferRange")'

            rows_to_delete = range(row2 + len(stock_shares_df), 180)
            for row in rows_to_delete:
                sheet.api.Rows(row).Delete()

            next_monitor_path = monitor_path.replace(today, next_trading_day)
            retry_save_excel(wb=wb, file_path=next_monitor_path)
            wb.close()
            app.quit()
            app.kill()
            print('[Monitor Update] Updated successfully')

        except Exception as e:
            print(e)
            print('[Alert!! Monitor Update] Update failed, retry in 10 seconds')
            time.sleep(10)
            self.update_monitor_next_trading_day(today)

        self.send_email()

    @staticmethod
    def send_email():
        Mail().send(
            subject=f'Monitor next trading day updated, archive today monitor in 2 min',
            body_content='',
            receivers=[R.staff['wu']]
        )
        time.sleep(120)

    def renew_stock_list(self, today):
        try:
            stock_shares_df = pd.read_csv(
                rf'{self.summary_dir}/stock_shares_{today}.csv', index_col=0).reset_index(drop=False)
            tag_pos_df = pd.read_csv(
                rf'{self.summary_dir}/tag_pos_{today}.csv', index_col=0,).reset_index(drop=False)
            print('get stock_shares_df & tag_pos')
            return stock_shares_df, tag_pos_df
        except Exception as e:
            print(e)
            print('[Next trading day stock list]Update failed, retry in 20 seconds')
            time.sleep(20)
            self.renew_stock_list(today)

    def archive_monitor_today(self, today):
        monitor_path = rf'{self.monitor_dir}/monitor_{today}_formula.xlsx'
        try:
            df = self.get_refreshed_data(monitor_path)
            df.index = df.index + 1
            df = df.applymap(lambda x: str(x) if isinstance(x, datetime.time) else x)
            df.columns = [chr(ord('A') + i) for i in range(len(df.columns))]
            app = xw.App(visible=False, add_book=False)
            wb = xw.books.open(monitor_path)
            sheet = wb.sheets['monitor目标持仓']

            for index in df.index:
                for col in df.columns:
                    sheet.range(f'{col}{index}').value = df.loc[index, col]

            retry_save_excel(wb=wb, file_path=monitor_path.replace('_formula', ''))

            wb.close()
            app.quit()
            print('Archive today rolling_check successfully')
        except Exception as e:
            print(e)
            print('Retry archive today rolling_check in 10 seconds')
            time.sleep(10)
            self.archive_monitor_today(today)

    def get_refreshed_data(self, monitor_path):
        df = pd.read_excel(monitor_path, sheet_name=0, index_col=None, header=None)
        if (df == 'Refreshing').any().any():
            print('Monitor data is refreshing, wait for 10 seconds to retry for archiving')
            self.get_refreshed_data(monitor_path)
        else:
            print('Monitor data refreshed and ready to be archived')
            return df


if __name__ == '__main__':
    CnnDailyRecord().update_monitor()
