#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/25 11:14
# @Author  : Suying
# @Site    : 
# @File    : talang_recorder.py

import time

import numpy as np
import pandas as pd
import xlwings as xw
import rqdatac as rq

from record.account_info import read_terminal_info
from record.get_clearing_info import SettleInfo
from util.utils import find_index_loc_in_excel

class TalangRecorder:
    def __init__(self, account_path, monitor_path, date=None, adjust=None):
        self.date = pd.to_datetime(date).strftime('%Y%m%d') if date is not None else time.strftime('%Y%m%d')
        self.account_path = account_path
        self.monitor_path = monitor_path
        self.adjust = adjust
        print('TalangRecorder initialized!')

    def update(self):
        rq.init()
        self.update_account(account='踏浪1号')
        self.update_account(account='踏浪2号')
        self.update_account(account='踏浪3号')

    def update_account(self, account):
        index_ret = self.get_index_ret(sheet_name=account)
        if self.adjust == '导出单':
            account_info_dict = read_terminal_info(date=self.date, account=account)
        else:
            account_info_dict = SettleInfo(date=self.date).get_settle_info(account=account)


        self.input_talang_account_cell_value(
            sheet_name=account,
            account_info_dict=account_info_dict,
            index_ret=index_ret
        )



    def input_talang_account_cell_value(self, sheet_name, account_info_dict, index_ret):
        app = xw.App(visible=False, add_book=False)
        print('Generate excel pid:', app.pid)

        wb = app.books.open(self.account_path)
        sheet = wb.sheets[sheet_name]

        row_to_fill = find_index_loc_in_excel(self.account_path, sheet_name, self.date)

        sheet.range(f'A{row_to_fill}').value = self.date
        sheet.range(f'B{row_to_fill}').value = account_info_dict['股票权益']  # 总资产
        sheet.range(f'C{row_to_fill}').formula = f'=B{row_to_fill}-B{row_to_fill - 1}-O{row_to_fill}'  # 当日盈亏
        sheet.range(f'D{row_to_fill}').formula = f'=C{row_to_fill}/B{row_to_fill - 1}'  # 当日盈亏率
        sheet.range(f'E{row_to_fill}').value = index_ret  # 指数收益率
        sheet.range(f'F{row_to_fill}').formula = f'=D{row_to_fill}-E{row_to_fill}'  # 当日超额
        sheet.range(f'G{row_to_fill}').formula = f'=G{row_to_fill - 1}*(1+D{row_to_fill})'  # 多头净值
        sheet.range(f'H{row_to_fill}').formula = f'=H{row_to_fill - 1}*(1+E{row_to_fill})'  # 指数净值
        sheet.range(f'I{row_to_fill}').formula = f'=G{row_to_fill}/H{row_to_fill}-1'  # 累计超额
        sheet.range(f'J{row_to_fill}').formula = f'=(1+I{row_to_fill})/(1+MAX($I$2:I{row_to_fill}))-1'  # 超额回撤
        sheet.range(f'K{row_to_fill}').value = account_info_dict['股票市值']  # 总市值
        sheet.range(f'L{row_to_fill}').formula = f'=K{row_to_fill}/B{row_to_fill}'  # 总仓位
        sheet.range(f'M{row_to_fill}').value = account_info_dict['成交额']  # 成交额
        sheet.range(f'N{row_to_fill}').formula = f'=M{row_to_fill}/B{row_to_fill - 1}'  # 双边换手率

        wb.save(self.account_path)
        wb.close()
        app.quit()
        app.kill()
        print(f'Sheet-{sheet_name} has been updated.')

    def get_index_ret(self, sheet_name):
        assert sheet_name in ['踏浪2号', '踏浪3号', '踏浪1号']
        monitor_df = pd.read_excel(self.monitor_path, sheet_name=0, index_col=False, header=None)
        index_code_dict = {
            '踏浪1号': '000688.SH',
            '踏浪2号': '000905.SH',
            '踏浪3号': '000852.SH',
        }

        index_ret = get_value(monitor_df, index_code_dict[sheet_name], 0, 1)
        print(sheet_name,'对标指数', index_code_dict[sheet_name],'的收益', index_ret)
        return index_ret

def get_value(df, string, i, j):
    loc = np.where(df.values == string)
    return df.iloc[loc[0][0] + i, loc[1][0] + j]