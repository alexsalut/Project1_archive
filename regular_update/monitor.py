import os.path
import time
import datetime

import xlwings as xw
import pandas as pd

from util.utils import retry_save_excel
from util.trading_calendar import TradingCalendar
from util.file_location import FileLocation
from util.send_email import Mail, R

class Monitor:
    monitor_dir = FileLocation.remote_monitor_dir
    summary_dir = FileLocation.remote_summary_dir
    dataset = {}
    seq = '*' * 25

    def update(self, today=None):
        print(f'\n{self.seq * 2} Update Monitor {self.seq * 2}')
        self.collect_related_data(today)
        self.update_next_trading_day()
        self.archive_today()

        print(f'{self.seq * 2} Monitor Daily Update is Done! {self.seq * 2}\n')

    def collect_related_data(self, today, starting_row=6):
        print(f'{self.seq} Collect Related Data {self.seq}')
        formatted_today = time.strftime('%Y%m%d') if today is None else today
        next_trading_day = TradingCalendar().get_n_trading_day(formatted_today, 1).strftime('%Y%m%d')

        tag_pos_path = rf'{self.summary_dir}/tag_pos_{formatted_today}.csv'
        stock_shares_path = rf'{self.summary_dir}/stock_shares_{formatted_today}.csv'

        tag_pos_df = pd.read_csv(tag_pos_path, index_col=0).reset_index(drop=False)

        self.dataset = {
            'today': formatted_today,
            'next_trading_day': TradingCalendar().get_n_trading_day(formatted_today, 1).strftime('%Y%m%d'),
            'template_path': rf'{self.monitor_dir}/monitor_template.xlsx',
            'monitor_path': rf'{self.monitor_dir}/monitor_{formatted_today}_formula.xlsx',
            'archive_path': rf'{self.monitor_dir}/monitor_{formatted_today}.xlsx',
            'next_monitor_path': rf'{self.monitor_dir}/monitor_{next_trading_day}_formula.xlsx',
            'tag_pos_df': tag_pos_df,
            'stock_shares_df': pd.read_csv(stock_shares_path, index_col=0).reset_index(drop=False),
            # tag_pos_df第一行在monitor表格中的行数
            'row1': starting_row,
            # stock_shares_df第一行在表格中的行数
            'row2': starting_row + len(tag_pos_df) + 3,
        }

    def update_next_trading_day(self):
        print(f'{self.seq} Update Next Trading Day {self.seq}')

        template_path = self.dataset['template_path']
        next_monitor_path = self.dataset['next_monitor_path']
        if not os.path.exists(next_monitor_path):
            app = xw.App(visible=False, add_book=False)
            print('Generate excel pid:', app.pid)
            app.display_alerts = False
            app.screen_updating = False
            wb = app.books.open(template_path)

            sheet = wb.sheets[0]
            self.clear_previous_rows(sheet)
            self.update_sheet_value(sheet)


            retry_save_excel(wb=wb, file_path=next_monitor_path)
            wb.close()
            app.quit()
            app.kill()
            print('*' * 25, 'Next Monitor Updated, Archive in 2 mins', '*' * 25)
            Mail().send(
                subject=f'Archive today monitor',
                body_content=f'{next_monitor_path} 更新完成',
                receivers=[R.staff['zhou']]
            )
            time.sleep(120)
        else:
            print(f'{next_monitor_path} already exists, no need to update')

    def update_sheet_value(self, sheet):
        row1 = self.dataset['row1']
        row2 = self.dataset['row2']
        tag_pos_df = self.dataset['tag_pos_df']
        stock_shares_df = self.dataset['stock_shares_df']
        next_trading_day = self.dataset['next_trading_day']

        sheet['B1'].value = next_trading_day
        for index in tag_pos_df.index:
            sheet[f'B{row1 + index}'].value = tag_pos_df.loc[index, 'index']

        for index in stock_shares_df.index:
            row = row2 + index
            sheet[f'A{row}'].value = stock_shares_df.loc[index, 'index']
            sheet[f'B{row}'].formula = f'=EM_S_INFO_NAME(A{row})'
            sheet[f'C{row}'].value = stock_shares_df.loc[index, '0']
            sheet[f'D{row}'].formula = f'=EM_S_INFO_INDUSTRY_SW2021(A{row},"1")'
            sheet[f'E{row}'].formula = f'=EM_S_FREELIQCI_VALUE(A{row},B1,100000000)'
            sheet[f'F{row}'].formula = f'=EM_S_VAL_MV2(A{row},B1,100000000)'
            sheet[f'G{row}'].formula = f'=RTD("em.rtq",,A{row},"Time")'
            sheet[f'H{row}'].formula = f'=RTD("em.rtq",,A{row},"DifferRange")'

    def clear_previous_rows(self, sheet):
        row2 = self.dataset['row2']
        rows_to_delete = range(row2, 180)
        for row in rows_to_delete:
            sheet.api.Rows(row).Delete()

    def archive_today(self):
        print(f'{self.seq} Archive Today Monitor {self.seq}')
        archive_path = self.dataset['archive_path']
        if not os.path.exists(archive_path):
            monitor_values_df = self.get_monitor_values_df(self.dataset['monitor_path'])

            app = xw.App(visible=False, add_book=False)
            wb = xw.books.open(self.dataset['monitor_path'])
            sheet = wb.sheets['monitor目标持仓']

            for index in monitor_values_df.index:
                for col in monitor_values_df.columns:
                    sheet.range(f'{col}{index}').value = monitor_values_df.loc[index, col]

            retry_save_excel(wb=wb, file_path=archive_path)
            wb.close()
            app.quit()
            app.kill()
        else:
            print(f'{archive_path} already exists, no need to archive')

    def get_monitor_values_df(self, monitor_path):
        df = pd.read_excel(monitor_path, sheet_name=0, index_col=None, header=None)
        if (df == 'Refreshing').any().any():
            print('Monitor values are refreshing, wait for 10 seconds to retry for archiving')
            self.get_monitor_values_df(monitor_path)
        else:
            print('Monitor values refreshed and ready to be archived')
            df.index = df.index + 1
            df = df.applymap(lambda x: str(x) if isinstance(x, datetime.time) else x)
            df.columns = [chr(ord('A') + i) for i in range(len(df.columns))]
            return df

if __name__ == '__main__':
    Monitor().update(today='20231130')
