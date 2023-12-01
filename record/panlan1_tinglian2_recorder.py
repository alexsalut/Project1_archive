#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/25 11:19
# @Author  : Suying
# @Site    : 
# @File    : panlan1_tinglian2_recorder.py

import time

import xlwings as xw
import pandas as pd

from util.file_location import FileLocation
from record.account_info import read_terminal_info
from record.get_clearing_info import SettleInfo
from util.utils import find_index_loc_in_excel

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

        if self.adjust == '导出单':
            account_info = read_terminal_info(self.formatted_date2, self.account)
        else:
            account_info = SettleInfo(date=self.formatted_date1).get_settle_info(account=self.account)

        row_to_fill = find_index_loc_in_excel(self.account_path, self.account, self.formatted_date1)
        sheet.range(f'A{row_to_fill}').value = self.formatted_date1
        sheet.range(f'B{row_to_fill}').formula = f'=H{row_to_fill}+N{row_to_fill}'  # 总资产
        sheet.range(f'C{row_to_fill}').formula = f'=I{row_to_fill}+O{row_to_fill}'
        sheet.range(f'D{row_to_fill}').formula = f'=C{row_to_fill}/(B{row_to_fill - 1})'  # 当日收益率
        sheet.range(f'E{row_to_fill}').formula = f'=(E{row_to_fill - 1}+1)*(1+D{row_to_fill})-1'  # 累计收益率
        sheet.range(f'G{row_to_fill}').formula = f'=(1+E{row_to_fill})/(1+MAX($E$2:E{row_to_fill}))-1'  # 累计回撤
        sheet.range(f'H{row_to_fill}').value = account_info['股票权益']
        sheet.range(f'I{row_to_fill}').formula = f'=H{row_to_fill}-H{row_to_fill - 1}-P{row_to_fill}'
        sheet.range(f'J{row_to_fill}').value = account_info['股票市值']
        sheet.range(f'K{row_to_fill}').formula = f'=J{row_to_fill}/H{row_to_fill}'
        sheet.range(f'L{row_to_fill}').value = account_info['成交额']
        sheet.range(f'M{row_to_fill}').formula = f'=L{row_to_fill}/H{row_to_fill - 1}'
        sheet.range(f'N{row_to_fill}').value = account_info['期权权益']
        sheet.range(f'O{row_to_fill}').formula = f'=N{row_to_fill}-N{row_to_fill - 1}-Q{row_to_fill}'

        wb.save(self.account_path)
        wb.close()
        app.quit()
        app.kill()
        print(f'Sheet-{self.account} has been updated.')



