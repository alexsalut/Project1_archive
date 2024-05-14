#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/5/8 16:32
# @Author  : Suying
# @Site    : 
# @File    : tinglian1_recorder.py

import time

import xlwings as xw
import pandas as pd

from util.file_location import FileLocation
from record.get_terminal_info import read_terminal_info
from record.get_clearing_info import SettleInfo
from util.utils import find_index_loc_in_excel


class Tinglian1Recorder:
    def __init__(self, account_path, date=None, adjust=None):
        self.date = pd.to_datetime(date).strftime("%Y%m%d") if date is not None else time.strftime('%Y%m%d')
        self.account_path = account_path
        self.adjust = adjust


    def record_account(self):
        sep = '*'*16
        print(f'{sep} Start to record account 听涟1号 {sep}')
        app = xw.App(visible=False, add_book=False)
        print('Generate excel pid:', app.pid)
        wb = xw.books.open(self.account_path)
        sheet = wb.sheets['听涟1号']

        if self.adjust == '导出单':
            account_info = read_terminal_info(self.date, '听涟1号')
        else:
            account_info = SettleInfo(date=self.date).get_settle_info(account='听涟1号')

        row_to_fill = find_index_loc_in_excel(self.account_path, '听涟1号', self.date)
        sheet.range(f'A{row_to_fill}').value = self.date
        sheet.range(f'B{row_to_fill}').formula = f'=H{row_to_fill}+N{row_to_fill}'  # 总资产
        sheet.range(f'C{row_to_fill}').formula = f'=I{row_to_fill}+O{row_to_fill}' #当日盈亏
        sheet.range(f'D{row_to_fill}').formula = f'=C{row_to_fill}/(B{row_to_fill - 1})'  # 当日收益率
        sheet.range(f'E{row_to_fill}').formula = f'=(E{row_to_fill - 1}+1)*(1+D{row_to_fill})-1'  # 累计收益率
        sheet.range(f'G{row_to_fill}').formula = f'=(1+E{row_to_fill})/(1+MAX($E$2:E{row_to_fill}))-1'  # 累计回撤

        sheet.range(f'H{row_to_fill}').value = account_info['股票权益']
        sheet.range(f'I{row_to_fill}').formula = f'=H{row_to_fill}-H{row_to_fill - 1}-Q{row_to_fill}'
        sheet.range(f'J{row_to_fill}').value = account_info['股票市值']
        sheet.range(f'K{row_to_fill}').formula = f'=J{row_to_fill}/H{row_to_fill}'
        sheet.range(f'L{row_to_fill}').value = account_info['股票成交额']
        sheet.range(f'M{row_to_fill}').formula = f'=L{row_to_fill}/H{row_to_fill - 1}'

        sheet.range(f'N{row_to_fill}').value = account_info['期货权益']
        sheet.range(f'O{row_to_fill}').formula = f'=N{row_to_fill}-N{row_to_fill - 1}-R{row_to_fill}'
        sheet.range(f'P{row_to_fill}').value = 1 - account_info['期货市值']/account_info['股票市值']

        wb.save(self.account_path)
        wb.close()
        app.quit()
        app.kill()
        print(f'Sheet-听涟1号 has been updated.')