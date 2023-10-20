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


class TalangRecorder:
    def __init__(self, account_path, date=None):
        self.date = pd.to_datetime(date).strftime('%Y%m%d') if date is not None else time.strftime('%Y%m%d')
        self.account_path = account_path

    def record_talang(self):
        self.record_account_talang(sheet_name='踏浪1号')
        self.record_account_talang(sheet_name='踏浪2号')
        self.record_account_talang(sheet_name='踏浪3号')

    def record_account_talang(self, sheet_name):
        index_ret = self.get_index_ret(sheet_name=sheet_name)
        talang_dict = {
            '踏浪2号': 'talang2',
            '踏浪3号': 'talang3',
            '踏浪1号': 'talang1'
        }

        account = talang_dict[sheet_name]
        account_info_s = read_account_info(date=self.date, account=account)

        try:
            self.input_talang_account_cell_value(
                sheet_name=sheet_name,
                account_info_s=account_info_s,
                index_ret=index_ret
            )
        except Exception as e:
            print(e)
            print(f'{self.account_path} with sheet name {sheet_name} updating failed, retry in 10 seconds')
            time.sleep(10)
            self.record_account_talang(sheet_name=sheet_name)

    def input_talang_account_cell_value(self, sheet_name, account_info_s, index_ret):
        # index_code_dict = {
        #     '踏浪2号': '"000905.SH"',
        #     '踏浪3号': '"000852.SH"',
        #     '踏浪1号': '"000688.SH"'
        # }

        app = xw.App(visible=False, add_book=False)
        wb = app.books.open(self.account_path)
        time.sleep(10)
        sheet = wb.sheets[sheet_name]
        last_row = sheet.cells(sheet.cells.last_cell.row, 1).end('up').row + 1
        sheet.range(f'A{last_row}').value = self.date  # date
        sheet.range(f'B{last_row}').value = account_info_s['股票权益']  # 总资产
        sheet.range(f'C{last_row}').formula = f'=B{last_row}-B{last_row - 1}-O{last_row}'  # 当日盈亏
        sheet.range(f'D{last_row}').formula = f'=C{last_row}/B{last_row - 1}'  # 当日盈亏率
        sheet.range(f'E{last_row}').formula = index_ret  # 指数收益率
        sheet.range(f'F{last_row}').formula = f'=D{last_row}-E{last_row}'  # 当日超额
        sheet.range(f'G{last_row}').formula = f'=G{last_row - 1}*(1+D{last_row})'  # 多头净值
        sheet.range(f'H{last_row}').formula = f'=H{last_row - 1}*(1+E{last_row})'  # 指数净值
        sheet.range(f'I{last_row}').formula = f'=G{last_row}/H{last_row}-1'  # 累计超额
        sheet.range(f'J{last_row}').formula = f'=(1+I{last_row})/(1+MAX($I$2:I{last_row}))-1'  # 超额回撤
        sheet.range(f'K{last_row}').value = account_info_s['股票市值']  # 总市值
        sheet.range(f'L{last_row}').formula = f'=K{last_row}/B{last_row}'  # 总仓位
        sheet.range(f'M{last_row}').value = account_info_s['成交额']  # 成交额
        sheet.range(f'N{last_row}').formula = f'=M{last_row}/B{last_row - 1}'  # 双边换手率

        wb.save(self.account_path)
        wb.close()
        app.quit()
        print(f'{self.account_path} with sheet name {sheet_name} updating finished')

    @staticmethod
    def get_index_ret(sheet_name):
        assert sheet_name in ['踏浪2号', '踏浪3号', '踏浪1号']
        index_code_dict = {
            '踏浪2号': '000905.SH',
            '踏浪3号': '000852.SH',
            '踏浪1号': '000688.SH'
        }

        index_code = index_code_dict[sheet_name]
        rq.init()
        order_book_ids = rq.id_convert(index_code)
        index_ret = rq.get_live_minute_price_change_rate(order_book_ids).iloc[-1, 0]
        print(f'{index_code} return is {index_ret:.2%}')
        return index_ret


if __name__ == '__main__':
    m = TalangRecorder(account_path=rf'C:\Users\Yz02\Desktop\strategy_update\cnn策略观察_20231019.xlsx',
                       date='20231019')
    m.record_account_talang(sheet_name='踏浪1号')
