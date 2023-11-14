#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/10 15:58
# @Author  : Suying
# @Site    : 
# @File    : gen_weekly_report.py

import os
import shutil

import pandas as pd
import xlwings as xw

from datetime import datetime, timedelta
from weekly_product_report.gen_stats import ProductStats


class WeeklyReport:
    def __init__(self, end=None):
        self.dir = rf'{os.path.expanduser("~")}\Desktop\产品每周汇总'
        os.makedirs(self.dir, exist_ok=True)

        self.end = end if end is not None else self.get_last_friday()
        self.start = (pd.to_datetime(self.end) - timedelta(days=7)).strftime('%Y%m%d')
        self.last_report_path = rf'{self.dir}\\衍舟业绩周报_{self.start}.xlsx'
        self.report_path = rf'{self.dir}\\衍舟业绩周报_{self.end}.xlsx'

        self.enhance_cols = {
            '累计净值': 'D',
            '当周收益': 'E',
            '当周超额': 'F',
            '年化超额': 'G',
            '超额最大回撤': 'H',
        }
        self.hedge_cols = {
            '累计净值': 'D',
            '当周收益': 'E',
            '年化收益': 'F',
            '历史最大回撤': 'H',
        }
        self.product_type_dict = {
            '指增': ['踏浪1号', '踏浪2号', '踏浪3号'],
            '对冲套利': ['听涟2号', '盼澜1号', '弄潮1号', '弄潮2号']
        }
        self.public_index_dict = {
            '踏浪1号': 3,
            '踏浪2号': 4,
            '踏浪3号': 5,
            '听涟2号': 7,
            '弄潮2号': 8,
        }
        self.private_index_dict = {
            '踏浪1号': 3,
            '踏浪2号': 4,
            '踏浪3号': 5,
            '听涟2号': 7,
            '盼澜1号': 8,
            '弄潮1号': 9,
            '弄潮2号': 10,
        }

    def gen_report(self):
        # self.copy_last_file()
        shutil.copyfile(src=self.last_report_path, dst=self.report_path)
        stats = ProductStats(end=self.end).get_all_stats()
        self.gen_separate_report(stats, sheet_name='公开版')
        self.gen_separate_report(stats, sheet_name='内部版')

    def copy_last_file(self):
        app = xw.App(visible=False, add_book=False)
        wb = app.books.open(self.last_report_path)
        wb.save(self.report_path)
        wb.close()
        app.quit()
        print(f'Copy {self.last_report_path} to {self.report_path} successfully')

    def gen_separate_report(self, stats, sheet_name='公开版'):
        app = xw.App(visible=False, add_book=False)
        wb = app.books.open(self.report_path)
        sheet = wb.sheets[sheet_name]
        product_index_dict = self.public_index_dict if sheet_name == '公开版' else self.private_index_dict
        sheet.range('B1').value = f'业绩周报【' \
                                  f'{self.start[:4]}年' \
                                  f'{self.start[4:6]}月' \
                                  f'{self.start[6:]}日' \
                                  f'-' \
                                  f'{self.end[:4]}年' \
                                  f'{self.end[4:6]}月' \
                                  f'{self.end[6:]}日' \
                                  f'】'

        for product, product_index in product_index_dict.items():
            product_cols = self.enhance_cols if product in self.product_type_dict['指增'] else self.hedge_cols
            self.input_product_stats(sheet, product_index, product_cols, stats[product])

        wb.save(self.report_path)
        wb.close()
        app.quit()
        print('Sheet', sheet_name, 'generated')

    def input_product_stats(self, sheet, product_index, product_cols, product_stats):
        for col in product_cols.keys():
            sheet.range(f'{product_cols[col]}{product_index}').value = product_stats[col]

    def get_last_friday(self):
        today = datetime.today()
        last_friday = today - timedelta(days=today.weekday() + 3)
        return last_friday.strftime('%Y%m%d')


if __name__ == '__main__':
    WeeklyReport().gen_report()
