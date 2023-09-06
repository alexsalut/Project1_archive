import time
import os

import pandas as pd
import xlwings as xw

from EmQuantAPI import c
from account import read_account_info
from utils import send_email, retry_save_excel


class Account:
    def __init__(self, date=None):
        self.date = date if date is not None else time.strftime('%Y%m%d')
        self.account_path = r'C:\Users\Yz02\Desktop\strategy_update\cnn策略观察.xlsx'
        self.monitor_path = rf'C:\Users\Yz02\Desktop\strategy_update\monitor_{self.date}.xlsx'
        self.remote_account_path = r'\\192.168.1.116\target_position\monitor\cnn策略观察.xlsx'

    def account_update(self):
        self.account_monitor_update(sheet_name='单策略超额')
        self.account_monitor_update(sheet_name='多策略超额')
        self.account_talang_update(sheet_name='踏浪2号')
        self.account_talang_update(sheet_name='踏浪3号')
        # self.account_remote_update()
        send_email(subject='[CNN 策略观察] 更新完成', content=None)

    def account_remote_update(self):
        app = xw.App(visible=False, add_book=False)
        wb = xw.books.open(self.account_path)
        wb.save(self.remote_account_path)
        wb.close()
        app.quit()

    def account_talang_update(self, sheet_name):
        try:
            index_ret = pd.read_excel(self.account_path, sheet_name=sheet_name, index_col=0).iloc[0,16]
        except ValueError:
            print(f'{self.account_path} with sheet name {sheet_name} not found, retry in 1 minute')
            time.sleep(60)
            self.account_talang_update(sheet_name=sheet_name)

        if sheet_name == '踏浪2号':
            account_info_s = read_account_info(date=self.date, account='tanglang2')
        elif sheet_name == '踏浪3号':
            account_info_s = read_account_info(date=self.date, account='tanglang3')
        else:
            raise

        app = xw.App(visible=False, add_book=False)
        wb = xw.books.open(self.account_path)
        sheet = wb.sheets[sheet_name]
        last_row = sheet.cells(sheet.cells.last_cell.row, 1).end('up').row+1

        sheet.range(f'A{last_row}').value = self.date  # date
        sheet.range(f'B{last_row}').value = account_info_s['总资产']  # 总资产
        sheet.range(f'C{last_row}').formula = f'=B{last_row}-B{last_row-1}-O{last_row-1}' # 当日盈亏
        sheet.range(f'D{last_row}').formula = f'=C{last_row}/(B{last_row-1}+O{last_row-1})' # 当日盈亏率
        sheet.range(f'E{last_row}').value = index_ret # 指数收益率
        sheet.range(f'F{last_row}').formula = f'=D{last_row}-E{last_row}' # 当日超额
        sheet.range(f'G{last_row}').formula = f'=G{last_row-1}*(1+D{last_row})' # 多头净值
        sheet.range(f'H{last_row}').formula = f'=H{last_row-1}*(1+E{last_row})' # 指数净值
        sheet.range(f'I{last_row}').formula = f'=G{last_row}/H{last_row}-1' # 累计超额
        sheet.range(f'J{last_row}').formula = f'=I{last_row}-MAX(I2:I{last_row})' # 超额回撤
        sheet.range(f'K{last_row}').value = account_info_s['股票总市值']  # 总市值
        sheet.range(f'L{last_row}').formula = f'=K{last_row}/B{last_row}' # 总仓位
        sheet.range(f'M{last_row}').value = account_info_s['成交额']  # 成交额
        sheet.range(f'N{last_row}').formula = f'=M{last_row}/B{last_row-1}' # 双边换手率

        retry_save_excel(wb=wb, file_path=self.account_path)
        wb.close()
        app.quit()

    def account_monitor_update(self, sheet_name):
        monitor_data = self.get_monitor_data()
        try:
            pd.read_excel(self.account_path, sheet_name=sheet_name, index_col=0)
        except ValueError:
            print(f'{self.account_path} with sheet name {sheet_name} not found, retry in 1 minute')
            time.sleep(60)
            self.account_monitor_update(sheet_name=sheet_name)

        app = xw.App(visible=False, add_book=False)
        wb = xw.books.open(self.account_path)
        sheet = wb.sheets[sheet_name]
        last_row = sheet.cells(sheet.cells.last_cell.row, 1).end('up').row+1
        sheet.range(f'A{last_row}').value = self.date  # date
        if sheet_name == '单策略超额':
            sheet.range(f'B{last_row}').value = monitor_data['sub_strategy_ret']    # 子策略涨幅
        elif sheet_name == '多策略超额':
            sheet.range(f'B{last_row}').value = monitor_data['strategy_ret']  # 策略涨幅
        else:
            raise

        sheet.range(f'C{last_row}').value = monitor_data['kc50_ret'] # 科创50涨幅
        sheet.range(f'D{last_row}').value = sheet.range(f'B{last_row}').value - sheet.range(f'C{last_row}').value # 指增超额
        sheet.range(f'E{last_row}').formula = f'=SUM(D2:D{last_row})'  # 累计指增超额算术
        sheet.range(f'F{last_row}').formula = f'=F{last_row-1}*(1+B{last_row})' #多头净值
        sheet.range(f'G{last_row}').formula = f'=G{last_row-1}*(1+C{last_row})' #指数净值
        sheet.range(f'H{last_row}').formula = f'=F{last_row}/G{last_row}' #累计超额净值
        sheet.range(f'I{last_row}').formula = f'=H{last_row}-1' #累计超额-几何
        sheet.range(f'J{last_row}').formula = f'=H{last_row}/MAX(H2:H{last_row})-1' #超额回撤
        retry_save_excel(wb=wb, file_path=self.account_path)
        wb.close()
        app.quit()

    def get_monitor_data(self):
        try:
            monitor_df = pd.read_excel(self.monitor_path, sheet_name=0, index_col=0)
        except FileNotFoundError:
            print(f'{self.monitor_path} not found, retry in 1 minute')
            time.sleep(60)
            self.get_monitor_data()

        monitor_data = pd.Series(index=['kc50_ret', 'strategy_ret', 'sub_strategy_ret', 'excess_ret', 'sub_excess_ret'], dtype=float)
        monitor_data['kc50_ret'] = monitor_df.iloc[0, 1]
        monitor_data['strategy_ret'] = monitor_df.iloc[0, 7]
        monitor_data['sub_strategy_ret'] = monitor_df.iloc[2, 7]
        monitor_data['excess_ret'] = monitor_df.iloc[0, 8]
        monitor_data['sub_excess_ret'] = monitor_df.iloc[2, 8]
        return monitor_data





