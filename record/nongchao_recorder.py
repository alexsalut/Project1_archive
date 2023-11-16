#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/7 17:12
# @Author  : Suying
# @Site    : 
# @File    : nongchao_recorder.py

import time

import pandas as pd
import xlwings as xw

from record.account_info import read_terminal_info


class NongchaoRecorder:
    def __init__(self, account_path, date=None, adjust=None):
        self.date = pd.to_datetime(date).strftime('%Y%m%d') if date is not None else time.strftime('%Y%m%d')
        self.account_path = account_path
        self.adjust = adjust
        self.account_col = {
            '弄潮1号': {
                '中信普通账户': ['Z', 'AA', 'AB', 'AC'],
                '华泰普通账户': ['AD', 'AE', 'AF', 'AG'],
                '中信信用账户': ['N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y'],
            },
            '弄潮2号': {
                '华泰普通账户': ['Z', 'AA', 'AB', 'AC'],
                '华泰信用账户': ['N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y'],
            },
        }
        self.in_out_cash_col = {
            '弄潮1号': {
                '中信普通账户': 'AH',
                '华泰普通账户': 'AI',
                '中信信用账户': 'AJ',
            },
            '弄潮2号': {
                '华泰普通账户': 'AE',
                '华泰信用账户': 'AD',
            }
        }

        self.total_account_col = ['B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M']

    def record_nongchao(self):
        self.record_account_nongchao(sheet_name='弄潮1号')
        self.record_account_nongchao(sheet_name='弄潮2号')

    def record_account_nongchao(self, sheet_name):
        account_info_dict = read_terminal_info(date=self.date, account=sheet_name)
        app = xw.App(visible=False, add_book=False)
        print('Generate excel pid:', app.pid)

        wb = app.books.open(self.account_path)
        sheet = wb.sheets[sheet_name]
        if self.adjust is None:
            last_row = sheet.cells(sheet.cells.last_cell.row, 1).end('up').row + 1
        else:
            last_row = sheet.cells(sheet.cells.last_cell.row, 1).end('up').row

        account_col_dict = self.account_col[sheet_name]
        cash_col_dict = self.in_out_cash_col[sheet_name]
        cash_col_list = [col for col in cash_col_dict.values()]
        for account, col_list in account_col_dict.items():
            if '信用' in account:
                self.input_credit_account(sheet, col_list, account_info_dict[account], cash_col_dict[account], last_row)
            else:
                self.input_normal_account(sheet, col_list, account_info_dict[account], cash_col_dict[account], last_row)

        self.input_total_account(sheet, self.total_account_col, account_info_dict, cash_col_list, last_row)
        wb.save(self.account_path)
        wb.close()
        app.quit()  # safe?

    def input_normal_account(self, sheet, col_list, account_dict, cash_col, last_row):
        sheet.range(f'{col_list[0]}{last_row}').value = account_dict['账户净资产']
        sheet.range(f'{col_list[1]}{last_row}').formula = f'=({col_list[0]}{last_row}-{col_list[0]}{last_row - 1} - {cash_col}{last_row })'
        sheet.range(f'{col_list[2]}{last_row}').value = account_dict['账户证券市值']
        sheet.range(f'{col_list[3]}{last_row}').formula = f'=({col_list[2]}{last_row}/{col_list[0]}{last_row})'

    def input_credit_account(self, sheet, col_list, account_dict, cash_col, last_row):
        sheet.range(f'{col_list[0]}{last_row}').value = account_dict['账户净资产']
        sheet.range(f'{col_list[1]}{last_row}').value = account_dict['账户总负债']
        sheet.range(f'{col_list[2]}{last_row}').value = account_dict['融资负债']
        sheet.range(f'{col_list[3]}{last_row}').value = account_dict['融券负债']
        sheet.range(f'{col_list[4]}{last_row}').value = account_dict['融资融券费用']

        sheet.range(f'{col_list[5]}{last_row}').formula = f'=({col_list[0]}{last_row}-{col_list[0]}{last_row - 1}-{cash_col}{last_row})'

        sheet.range(f'{col_list[6]}{last_row}').value = account_dict['维担比例']
        sheet.range(f'{col_list[7]}{last_row}').value = account_dict['账户证券市值']
        sheet.range(f'{col_list[8]}{last_row}').value = account_dict['可转债市值']
        sheet.range(f'{col_list[9]}{last_row}').value = account_dict['多头证券市值']
        sheet.range(f'{col_list[10]}{last_row}').value = account_dict['多头现金类市值']
        sheet.range(f'{col_list[11]}{last_row}').formula = f'=1-({col_list[3]}{last_row}/{col_list[9]}{last_row})'

    def input_total_account(self, sheet, col_list, account_dict, cash_cols, last_row):
        sheet.range(f'A{last_row}').value = self.date
        sheet.range(f'{col_list[0]}{last_row}').value = sum([account['账户净资产'] for account in account_dict.values()])
        sheet.range(f'{col_list[1]}{last_row}').value = sum([account['账户总负债'] for account in account_dict.values() if '账户总负债' in account.keys()])
        sheet.range(f'{col_list[2]}{last_row}').formula = f'={col_list[1]}{last_row}/{col_list[0]}{last_row} + 1'
        sheet.range(f'{col_list[3]}{last_row}').value = sum(
            [account['可转债市值'] for account in account_dict.values()])
        sheet.range(f'{col_list[4]}{last_row}').value = sum([account['融券负债'] for account in account_dict.values() if '融券负债' in account.keys()])

        cash_string = ','.join([f'{cash_col}{last_row}' for cash_col in cash_cols])
        sheet.range(f'{col_list[5]}{last_row}').formula = f'={col_list[0]}{last_row}-{col_list[0]}{last_row - 1}-SUM({cash_string})'
        sheet.range(f'{col_list[6]}{last_row}').formula = f'={col_list[5]}{last_row}/{col_list[0]}{last_row - 1}'
        sheet.range(
            f'{col_list[7]}{last_row}').formula = f'=({col_list[7]}{last_row - 1}+1)*({col_list[6]}{last_row}+1)-1'
        sheet.range(f'{col_list[8]}{last_row}').formula = f'={col_list[7]}{last_row}+1'
        sheet.range(
            f'{col_list[9]}{last_row}').formula = f'={col_list[8]}{last_row}/MAX({col_list[8]}4:{col_list[8]}{last_row})-1'

        sheet.range(f'{col_list[10]}{last_row}').value = sum([account['成交额'] for account in account_dict.values()])
        sheet.range(f'{col_list[11]}{last_row}').formula = f'=({col_list[10]}{last_row}/{col_list[0]}{last_row})'


if __name__ == '__main__':
    NongchaoRecorder(account_path=r'C:\Users\Yz02\Desktop\strategy_update\衍舟策略观察_20231109.xlsx', date='20231108').record_nongchao()
    NongchaoRecorder(account_path=r'C:\Users\Yz02\Desktop\strategy_update\衍舟策略观察_20231109.xlsx', date='20231109').record_nongchao()