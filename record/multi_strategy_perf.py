#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/25 11:05
# @Author  : Suying
# @Site    : 
# @File    : multi_strategy_perf.py

import time

import pandas as pd
import xlwings as xw
import numpy as np


class MultiStrategyPerf:
    def __init__(self, account_path, monitor_path, date=None):
        self.date = date if date is not None else time.strftime('%Y%m%d')
        self.account_path = account_path
        self.monitor_path = monitor_path

    def update(self):
        print('\nUpdate multi-strategy performance...')
        monitor_data = self.get_monitor_data()
        self.fill_today_perf(monitor_data)

    def get_monitor_data(self):
        def get_value(df, string, i, j):
            loc = np.where(df.values == string)
            return df.iloc[loc[0][0] + i, loc[1][0] + j]

        monitor_df = pd.read_excel(self.monitor_path, sheet_name=0, index_col=False, header=None)
        monitor_data = pd.Series(
            data=[
                get_value(monitor_df, '000688.SH', 0, 1),
                get_value(monitor_df, '踏浪1号', 0, 1),
                get_value(monitor_df, 'I5R2_all_20', 0, 6),
                get_value(monitor_df, '踏浪1号', 0, 2),
                get_value(monitor_df, 'I5R2_all_20', 0, 7),
             ],
            index=['kc50_ret', 'strategy_ret', 'sub_strategy_ret', 'excess_ret', 'sub_excess_ret'],
            dtype=float,
        )

        if (monitor_data == 'Refreshing').any() is True:
            print('Monitor data is refreshing, wait for 10 seconds to retry for access')
            time.sleep(10)
            self.get_monitor_data()
        else:
            print('Read monitor data:', self.monitor_path)
            return monitor_data

    def fill_today_perf(self, monitor_data):
        sheet_name = '多策略超额'
        try:
            app = xw.App(visible=False, add_book=False)
            wb = app.books.open(self.account_path)
            sheet = wb.sheets[sheet_name]
            print('Generate excel pid:', app.pid)

            last_row = sheet.cells(sheet.cells.last_cell.row, 1).end('up').row + 1
            sheet.range(f'A{last_row}').value = self.date  # date
            sheet.range(f'B{last_row}').value = monitor_data['strategy_ret']  # 策略涨幅
            sheet.range(f'C{last_row}').value = monitor_data['kc50_ret']  # 科创50涨幅

            print(f'[{sheet_name}] 科创50收益率', monitor_data['kc50_ret'])
            sheet.range(f'D{last_row}').formula = f'=B{last_row}-C{last_row}'  # 指增超额
            sheet.range(f'E{last_row}').formula = f'=SUM(D2:D{last_row})'  # 累计指增超额算术
            sheet.range(f'F{last_row}').formula = f'=F{last_row - 1}*(1+B{last_row})'  # 多头净值
            sheet.range(f'G{last_row}').formula = f'=G{last_row - 1}*(1+C{last_row})'  # 指数净值
            sheet.range(f'H{last_row}').formula = f'=F{last_row}/G{last_row}'  # 累计超额净值
            sheet.range(f'I{last_row}').formula = f'=H{last_row}-1'  # 累计超额-几何
            sheet.range(f'J{last_row}').formula = f'=H{last_row}/MAX(H2:H{last_row})-1'  # 超额回撤
            wb.save(self.account_path)
            wb.close()
            app.quit()
            print(f'Sheet-{sheet_name} has been updated.')

        except Exception as e:
            print(e)
            print(f'Sheet {sheet_name} updated in failure, retry in 1 min: {self.account_path}')
            time.sleep(60)
            self.fill_today_perf(monitor_data)
