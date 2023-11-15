#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/25 11:14
# @Author  : Suying
# @Site    : 
# @File    : talang_recorder.py

import time

import pandas as pd
import xlwings as xw
import rqdatac as rq

from record.account_info import read_account_info
from account_check.get_clearing_info import SettleInfo


class TalangRecorder:
    def __init__(self, account_path, date=None, adjust=None):
        self.date = pd.to_datetime(date).strftime('%Y%m%d') if date is not None else time.strftime('%Y%m%d')
        self.account_path = account_path
        self.adjust = adjust

    def update(self):
        rq.init()
        self.update_account(account='踏浪1号')
        self.update_account(account='踏浪2号')
        self.update_account(account='踏浪3号')

    def update_account(self, account):
        index_ret = self.rq_get_index_ret(sheet_name=account)
        if self.adjust is None:
            account_info_dict = read_account_info(date=self.date, account=account)
        else:
            account_info_dict = SettleInfo(date=self.date).get_settle_info(account=account)

        try:
            self.input_talang_account_cell_value(
                sheet_name=account,
                account_info_dict=account_info_dict,
                index_ret=index_ret
            )

        # Which exception ?
        except Exception as e:
            print(e)
            print(f'{self.account_path} with sheet name {account} updating failed, retry in 10 seconds')
            time.sleep(10)
            self.update_account(account)

    def input_talang_account_cell_value(self, sheet_name, account_info_dict, index_ret):
        app = xw.App(visible=False, add_book=False)
        print('Generate excel pid:', app.pid)

        wb = app.books.open(self.account_path)
        sheet = wb.sheets[sheet_name]
        if self.adjust is None:
            last_row = sheet.cells(sheet.cells.last_cell.row, 1).end('up').row + 1
        else:
            last_row = sheet.cells(sheet.cells.last_cell.row, 1).end('up').row

        sheet.range(f'A{last_row}').value = self.date
        sheet.range(f'B{last_row}').value = account_info_dict['股票权益']  # 总资产
        sheet.range(f'C{last_row}').formula = f'=B{last_row}-B{last_row - 1}-O{last_row}'  # 当日盈亏
        sheet.range(f'D{last_row}').formula = f'=C{last_row}/B{last_row - 1}'  # 当日盈亏率
        sheet.range(f'E{last_row}').value = index_ret  # 指数收益率
        sheet.range(f'F{last_row}').formula = f'=D{last_row}-E{last_row}'  # 当日超额
        sheet.range(f'G{last_row}').formula = f'=G{last_row - 1}*(1+D{last_row})'  # 多头净值
        sheet.range(f'H{last_row}').formula = f'=H{last_row - 1}*(1+E{last_row})'  # 指数净值
        sheet.range(f'I{last_row}').formula = f'=G{last_row}/H{last_row}-1'  # 累计超额
        sheet.range(f'J{last_row}').formula = f'=(1+I{last_row})/(1+MAX($I$2:I{last_row}))-1'  # 超额回撤
        sheet.range(f'K{last_row}').value = account_info_dict['股票市值']  # 总市值
        sheet.range(f'L{last_row}').formula = f'=K{last_row}/B{last_row}'  # 总仓位
        sheet.range(f'M{last_row}').value = account_info_dict['成交额']  # 成交额
        sheet.range(f'N{last_row}').formula = f'=M{last_row}/B{last_row - 1}'  # 双边换手率

        wb.save(self.account_path)
        wb.close()
        app.quit()
        print(f'Sheet-{sheet_name} has been updated.')

    def rq_get_index_ret(self, sheet_name):
        assert sheet_name in ['踏浪2号', '踏浪3号', '踏浪1号']
        index_code_dict = {
            '踏浪1号': '000688.SH',
            '踏浪2号': '000905.SH',
            '踏浪3号': '000852.SH',
        }

        index_code = index_code_dict[sheet_name]
        order_book_ids = rq.id_convert(index_code)

        def get_index_ret(_order_book_ids, date):
            index_ret_df = rq.get_price_change_rate(_order_book_ids, start_date=date, end_date=date)
            if index_ret_df is None:
                print(time.strftime('%X'),
                      f'RiceQuant has no data for {index_code}-{date} yet, retry in 5 min.')
                time.sleep(300)
                get_index_ret(order_book_ids, date)
            else:
                print(f'RiceQuant has got data for {index_code}-{date}: {index_ret_df.iloc[-1, 0]:.2%}')
                return index_ret_df.iloc[-1, 0]

        index_ret = get_index_ret(order_book_ids, self.date)
        return index_ret
