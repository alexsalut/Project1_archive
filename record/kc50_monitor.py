import os.path
import time
import numpy as np
import xlwings as xw
import pandas as pd

from util.utils import retry_save_excel, fill_in_stock_code
from util.trading_calendar import TradingCalendar
from util.file_location import FileLocation


class Monitor:
    monitor_dir = FileLocation.remote_monitor_dir
    summary_dir = FileLocation.remote_summary_dir
    dataset = {}
    seq = '*' * 25
    # tag_pos_df第一行在monitor表格中的行数
    starting_row = 6

    def update(self, today=None):
        today = pd.to_datetime(today).strftime('%Y%m%d') if today is not None else time.strftime('%Y%m%d')
        print(f'\n{self.seq * 2} Update Monitor {self.seq * 2}')
        self.collect_related_data(today)
        self.update_next_trading_day()

        print(f'{self.seq * 2} Monitor daily Update is Done! {self.seq * 2}\n')

    def collect_related_data(self, today):
        print(f'{self.seq} Collect Related Data {self.seq}')
        formatted_today = time.strftime('%Y%m%d') if today is None else today
        next_trading_day = TradingCalendar().get_n_trading_day(formatted_today, 1).strftime('%Y%m%d')
        tag_pos = self.read_pos_file(today)

        self.dataset = {
            'next_trading_day': TradingCalendar().get_n_trading_day(formatted_today, 1).strftime('%Y%m%d'),
            'template_path': rf'{self.monitor_dir}/monitor_template.xlsx',
            'next_monitor_path': rf'{self.monitor_dir}/monitor_{next_trading_day}.xlsx',
            'tag_pos': tag_pos,
        }
        return self.dataset

    def update_next_trading_day(self):
        print(f'{self.seq} Update Next Trading Day {self.seq}')

        template_path = self.dataset['template_path']
        next_monitor_path = self.dataset['next_monitor_path']
        next_trading_day = self.dataset['next_trading_day']
        strategy_pos = self.dataset['tag_pos']
        if not os.path.exists(next_monitor_path):
            app = xw.App(visible=False, add_book=False)
            print('Generate excel pid:', app.pid)
            app.display_alerts = False
            app.screen_updating = False
            wb = app.books.open(template_path)
            sheet = wb.sheets['monitor目标持仓']
            sheet.range('B1').value = next_trading_day

            for strategy, pos in strategy_pos.items():
                sheet = wb.sheets[strategy]
                clear_previous_rows(sheet)
                pos_reshaped = np.reshape(pos, (-1, 1))
                sheet.range(f'A2:A{1 + len(pos)}').value = pos_reshaped
                print(f'{strategy} updated')

            retry_save_excel(wb=wb, file_path=next_monitor_path)
            wb.close()
            app.quit()
            app.kill()
            print('*' * 25, 'Next Monitor Updated, Archive today now', '*' * 25)

        else:
            print(f'{next_monitor_path} already exists, no need to update')

    @staticmethod
    def read_pos_file(date):
        path = rf'\\192.168.1.116\target_position\summary\tag_pos_{date}.csv'
        pos_s = pd.read_csv(path, index_col=0, converters={'ticker': str})['strategy']
        strategy_lst = pos_s.unique().tolist()
        pos_dict = {
            strategy: fill_in_stock_code([str(stock).zfill(6) for stock in pos_s[pos_s == strategy].index.tolist()])
            for strategy in strategy_lst
        }
        return pos_dict


def clear_previous_rows(sheet):
    row2 = 2
    rows_to_delete = range(row2, 180)
    for row in rows_to_delete:
        sheet.range(f'A{row}').value = None
