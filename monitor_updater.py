import pandas as pd
import time
import os
import xlwings as xw
import openpyxl
from openpyxl import load_workbook


from utils import send_email, update_excel


class monitor_updater:
    def __init__(self, monitor_dir, remote_summary_dir, remote_monitor_dir):
        self.monitor_dir = monitor_dir
        self.remote_monitor_dir = remote_monitor_dir
        self.today = time.strftime('%Y%m%d')
        self.monitor_path = rf'{self.monitor_dir}/monitor_{self.today}.xlsx'
        self.remote_summary_dir = remote_summary_dir
        self.tomorrow = time.strftime('%Y%m%d', time.localtime(time.time() + 86400))

    def monitor_update(self):
        self.monitor_next_trading_day_update()
        self.monitor_next_day_check()
        self.monitor_today_archive()

    def monitor_today_archive(self):
        print()

    def monitor_next_day_check(self):
        if os.path.exists(rf'{self.monitor_dir}/monitor_{self.tomorrow}.xlsx'):
            send_email(subject='[Monitor Update]Next trading day monitor updated', content=None)
    def monitor_next_trading_day_update(self):

        app = xw.App(visible=False, add_book=False)
        app.display_alerts = False
        app.screen_updating = False
        wb = app.books.open(self.monitor_path)
        wb.save(rf'{self.monitor_dir}/monitor_{self.tomorrow}.xlsx')
        wb.close()
        app.quit()

        stock_shares_df, tag_pos_df = self.renew_stock_list()
        app = xw.App(visible=False, add_book=False)
        wb = xw.books.open(rf'{self.monitor_dir}/monitor_{self.tomorrow}.xlsx')
        sheet = wb.sheets[0]
        sheet['B1'].value = self.tomorrow
        for index in tag_pos_df.index:
            sheet[f'B{index+4}'].value = tag_pos_df.loc[index, 'index']
        for index in stock_shares_df.index:
            sheet[f'A{index+57}'].value = stock_shares_df.loc[index, 'index']
            sheet[f'C{index+57}'].value = stock_shares_df.loc[index, '0']
        wb.save()
        wb.close()
        app.quit()

        app = xw.App(visible=False, add_book=False)
        app.display_alerts = False
        app.screen_updating = False
        wb = app.books.open(rf'{self.monitor_dir}/monitor_{self.tomorrow}.xlsx')
        wb.save(rf'{self.remote_monitor_dir}/monitor_{self.tomorrow}.xlsx')
        wb.close()
        app.quit()


    def renew_stock_list(self):
        if os.path.exists(rf'{self.remote_summary_dir}\stock_shares_{self.today}.csv') & os.path.exists(rf'{self.remote_summary_dir}/tag_pos_{self.today}.csv'):
            stock_shares_df = pd.read_csv(rf'{self.remote_summary_dir}/stock_shares_{self.today}.csv', index_col=0).reset_index(drop=False)
            tag_pos_df = pd.read_csv(rf'{self.remote_summary_dir}/tag_pos_{self.today}.csv', index_col=0).reset_index(drop=False)
            return stock_shares_df, tag_pos_df
        else:
            send_email(subject='[Monitor Update]summary file not found', content=None)
            raise FileNotFoundError


if __name__ == '__main__':
    summary_dir = r'\\192.168.1.116\target_position\summary'

    monitor_dir = r'C:\Users\Yz02\Desktop\strategy_update'
    remote_dir = r'\\192.168.1.116\target_position\monitor'

    monitor_updater(
        monitor_dir=monitor_dir,
        remote_summary_dir=summary_dir,
        remote_monitor_dir=remote_dir,
    ).monitor_next_trading_day_update()





