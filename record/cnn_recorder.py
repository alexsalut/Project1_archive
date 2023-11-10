#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/25 11:05
# @Author  : Suying
# @Site    : 
# @File    : cnn_recorder.py

import time
import pandas as pd
import xlwings as xw
import numpy as np



class Cnn_Recorder:
    def __init__(self, account_path, monitor_path, date=None):
        self.date = date if date is not None else time.strftime('%Y%m%d')
        self.account_path = account_path
        self.monitor_path = monitor_path

    def cnn_recorder(self):
        self.record_cnn_account(sheet_name='多策略超额')
        self.record_cnn_account(sheet_name='单策略超额')

    def record_cnn_account(self, sheet_name):
        monitor_data = self.get_monitor_data()
        try:
            app = xw.App(visible=False, add_book=False)
            wb = app.books.open(self.account_path)
            sheet = wb.sheets[sheet_name]
            last_row = sheet.cells(sheet.cells.last_cell.row, 1).end('up').row + 1
            sheet.range(f'A{last_row}').value = self.date  # date
            if sheet_name == '单策略超额':
                sheet.range(f'B{last_row}').value = monitor_data['sub_strategy_ret']  # 子策略涨幅
            elif sheet_name == '多策略超额':
                sheet.range(f'B{last_row}').value = monitor_data['strategy_ret']  # 策略涨幅
            else:
                raise

            sheet.range(f'C{last_row}').value = monitor_data['kc50_ret']  # 科创50涨幅
            print(f'[{sheet_name}]科创50收益率', monitor_data['kc50_ret'])
            sheet.range(f'D{last_row}').formula = f'=B{last_row}-C{last_row}' # 指增超额
            sheet.range(f'E{last_row}').formula = f'=SUM(D2:D{last_row})'  # 累计指增超额算术
            sheet.range(f'F{last_row}').formula = f'=F{last_row - 1}*(1+B{last_row})'  # 多头净值
            sheet.range(f'G{last_row}').formula = f'=G{last_row - 1}*(1+C{last_row})'  # 指数净值
            sheet.range(f'H{last_row}').formula = f'=F{last_row}/G{last_row}'  # 累计超额净值
            sheet.range(f'I{last_row}').formula = f'=H{last_row}-1'  # 累计超额-几何
            sheet.range(f'J{last_row}').formula = f'=H{last_row}/MAX(H2:H{last_row})-1'  # 超额回撤
            wb.save(self.account_path)
            wb.close()
            app.quit()
            print(f'{self.account_path} with sheet name {sheet_name} updated successfully')
        except Exception as e:
            print(e)
            print(f'{self.account_path} with sheet name {sheet_name} updating failed, retry in 10 seconds')
            time.sleep(10)
            self.record_cnn_account(sheet_name=sheet_name)

    def get_monitor_data(self):
        monitor_df = pd.read_excel(self.monitor_path, sheet_name=0, index_col=False, header=None)

        def get_value(df, string, i, j):
            loc = np.where(df.values == string)
            return df.iloc[loc[0][0] + i, loc[1][0] + j]


        monitor_data = pd.Series(index=['kc50_ret', 'strategy_ret', 'sub_strategy_ret', 'excess_ret', 'sub_excess_ret'],
                                 data=[
                                     get_value(monitor_df, '000688.SH', 0, 1),
                                     get_value(monitor_df, '(踏浪1号）', 0, 1),
                                     get_value(monitor_df, 'I5R2_all_20', 0, 6),
                                     get_value(monitor_df, '(踏浪1号）', 0, 2),
                                     get_value(monitor_df, 'I5R2_all_20', 0, 7),
                                 ],
                                 dtype=float)

        if (monitor_data == 'Refreshing').any() is True:
            print('Account rolling_check data is refreshing, wait for 10 seconds to retry for access')
            self.get_monitor_data()
        else:
            print('Get account rolling_check data successfully')
            return monitor_data


if __name__ == '__main__':
    account_path = r'C:\Users\Yz02\Desktop\strategy_update\cnn策略观察_20210925.xlsx'
    monitor_path = r'C:\Users\Yz02\Desktop\strategy_update\monitor_20231108_formula.xlsx'
    Cnn_Recorder(account_path=account_path, monitor_path=monitor_path).cnn_recorder()
