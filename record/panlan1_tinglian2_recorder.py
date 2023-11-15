#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/25 11:19
# @Author  : Suying
# @Site    : 
# @File    : panlan1_tinglian2_recorder.py

import time

import xlwings as xw
import pandas as pd

from file_location import FileLocation
from record.account_info import read_account_info
from account_check.get_clearing_info import SettleInfo


class PanlanTinglianRecorder:
    def __init__(self, account_path, account, date=None, adjust=None):
        self.formatted_date1 = pd.to_datetime(date).strftime("%Y%m%d") if date is not None else time.strftime('%Y%m%d')
        self.formatted_date2 = pd.to_datetime(date).strftime("%Y-%m-%d") if date is not None else time.strftime(
            '%Y-%m-%d')
        self.account_path = account_path
        self.account = account
        self.adjust = adjust

        f = FileLocation()
        self.panlan_dir = f.account_info_dir_dict['盼澜1号']
        self.tinglian_dir = f.account_info_dir_dict['听涟2号 emc']

    def record_account(self):
        app = xw.App(visible=False, add_book=False)
        print('Generate excel pid:', app.pid)
        wb = xw.books.open(self.account_path)
        sheet = wb.sheets[self.account]

        if self.adjust is None:
            account_info = read_account_info(self.formatted_date2, self.account)
            last_row = sheet.cells(sheet.cells.last_cell.row, 1).end('up').row + 1
        else:
            account_info = SettleInfo(date=self.formatted_date1).get_settle_info(account=self.account)
            last_row = sheet.cells(sheet.cells.last_cell.row, 1).end('up').row

        sheet.range(f'A{last_row}').value = self.formatted_date1
        sheet.range(f'B{last_row}').formula = f'=H{last_row}+N{last_row}'  # 总资产
        sheet.range(f'C{last_row}').formula = f'=I{last_row}+O{last_row}'
        sheet.range(f'D{last_row}').formula = f'=C{last_row}/(B{last_row - 1})'  # 当日收益率
        sheet.range(f'E{last_row}').formula = f'=(E{last_row - 1}+1)*(1+D{last_row})-1'  # 累计收益率
        sheet.range(f'G{last_row}').formula = f'=(1+E{last_row})/(1+MAX($E$2:E{last_row}))-1'  # 累计回撤
        sheet.range(f'H{last_row}').value = account_info['股票权益']
        sheet.range(f'I{last_row}').formula = f'=H{last_row}-H{last_row - 1}-P{last_row}'
        sheet.range(f'J{last_row}').value = account_info['股票市值']
        sheet.range(f'K{last_row}').formula = f'=J{last_row}/H{last_row}'
        sheet.range(f'L{last_row}').value = account_info['成交额']
        sheet.range(f'M{last_row}').formula = f'=L{last_row}/H{last_row - 1}'
        sheet.range(f'N{last_row}').value = account_info['期权权益']
        sheet.range(f'O{last_row}').formula = f'=N{last_row}-N{last_row - 1}-Q{last_row}'

        wb.save(self.account_path)
        wb.close()
        app.quit()
        print(f'Sheet-{self.account} has been updated.')


if __name__ == '__main__':
    print()
