#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/25 11:19
# @Author  : Suying
# @Site    : 
# @File    : panlan1_recorder.py

import time
import xlwings as xw
import pandas as pd
from file_location import FileLocation as FL


class Panlan1Recorder:
    def __init__(self, account_path, date=None):
        self.date = pd.to_datetime(date).strftime("%Y-%m-%d") if date is not None else time.strftime('%Y-%m-%d')
        self.account_path = account_path
        self.panlan_dir = FL().account_info_dir_dict['panlan1']

    def record_panlan1(self):
        try:
            option_s = \
            pd.read_csv(rf'{self.panlan_dir}/OptionFund_{self.date}.csv', index_col=False).set_index('账户').loc[
                FL().option_account_code_dict['panlan1']]
            stock_s = \
            pd.read_csv(rf'{self.panlan_dir}/StockFund_{self.date}.csv', index_col=False).set_index('账户').loc[
                FL().stock_account_code_dict['panlan1']]
            transaction_df = \
                pd.read_csv(rf'{self.panlan_dir}/TransactionsStatisticsDaily_{self.date}.csv',
                            index_col=False).set_index(
                    '账户').loc[4082225]
            app = xw.App(visible=False, add_book=False)
            wb = xw.books.open(self.account_path)
            sheet = wb.sheets['盼澜1号']
            last_row = sheet.cells(sheet.cells.last_cell.row, 1).end('up').row + 1
            sheet.range(f'A{last_row}').value = pd.to_datetime(self.date).strftime("%Y%m%d")
            sheet.range(f'B{last_row}').formula = f'=H{last_row}+N{last_row}'  # 总资产
            sheet.range(f'C{last_row}').formula = f'=I{last_row}+O{last_row}'
            sheet.range(f'D{last_row}').formula = f'=C{last_row}/(B{last_row - 1})'  # 当日收益率
            sheet.range(f'E{last_row}').formula = f'=(E{last_row - 1}+1)*(1+D{last_row})-1'  # 累计收益率
            sheet.range(f'G{last_row}').formula = f'=(1+E{last_row})/(1+MAX($E$2:E{last_row}))-1'  # 累计回撤
            sheet.range(f'H{last_row}').value = stock_s['账户资产']
            sheet.range(f'I{last_row}').formula = f'=H{last_row}-H{last_row - 1}-P{last_row}'
            sheet.range(f'J{last_row}').value = stock_s['证券市值']
            sheet.range(f'K{last_row}').formula = f'=J{last_row}/H{last_row}'
            sheet.range(f'L{last_row}').value = transaction_df['成交额'].sum()
            sheet.range(f'M{last_row}').formula = f'=L{last_row}/H{last_row - 1}'
            sheet.range(f'N{last_row}').value = option_s['客户总权益']
            sheet.range(f'O{last_row}').formula = f'=N{last_row}-N{last_row - 1}-Q{last_row}'

            wb.save(self.account_path)
            wb.close()
            app.quit()
            print(f'{self.account_path} 盼澜1号 updating finished')
        except Exception as e:
            print(e)
            print(f'{self.account_path} 盼澜1号 updating failed. retry in 2 seconds')
            time.sleep(2)
            self.record_panlan1()
#
# if __name__ == '__main__':
#     Panlan1Recorder(rf'/盼澜1号.xlsx','20231010').record_panlan1()
