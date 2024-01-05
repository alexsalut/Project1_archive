#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/10 15:58
# @Author  : Suying
# @Site    : 
# @File    : gen_daily_report.py

import os
import shutil

import pandas as pd
import xlwings as xw

from datetime import datetime, timedelta
from weekly_product_report.gen_stats import ProductStats


class dailyReport:
    def __init__(self, start=None, end=None):
        self.dir = r'Z:\投研\数据\产品业绩\产品周报'
        os.makedirs(self.dir, exist_ok=True)

        self.end = end if end is not None else self.get_last_friday()
        self.start = (pd.to_datetime(self.end) - timedelta(days=7)).strftime('%Y%m%d') if start is None else start
        self.template_report_path = rf'{self.dir}\衍舟业绩周报_新模版.xlsx'
        self.report_path = rf'{self.dir}\衍舟业绩周报_{self.end}.xlsx'

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
        print('*'*32,f'Obtaining nav and generating stats...', '*'*32)
        stats = ProductStats().get_all_stats(self.start, self.end)
        print('*'*32,f'Generating {self.report_path}...', '*'*32)
        self.copy_template_file()
        shutil.copyfile(src=self.template_report_path, dst=self.report_path)

        self.gen_separate_report(stats, sheet_name='公开版')
        self.gen_separate_report(stats, sheet_name='内部版')

    def copy_template_file(self):
        app = xw.App(visible=False, add_book=False)
        wb = app.books.open(self.template_report_path)
        wb.save(self.report_path)
        wb.close()
        app.quit()
        app.kill()
        print(f'Copy {self.template_report_path} to {self.report_path} successfully')

    def gen_separate_report(self, stats, sheet_name='公开版'):
        print(f'Generating {sheet_name}...')
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
            print('Generating', product, '...')
            product_cols = self.enhance_cols if product in self.product_type_dict['指增'] else self.hedge_cols
            self.input_product_stats(sheet, product_index, product_cols, stats[product])
            print("Product", product, "generated")

        wb.save(self.report_path)
        wb.close()
        app.quit()
        app.kill()
        print('Sheet', sheet_name, 'generated')

    def input_product_stats(self, sheet, product_index, product_cols, product_stats):
        for col in product_cols.keys():
            sheet.range(f'{product_cols[col]}{product_index}').value = product_stats[col]

    def get_last_friday(self):
        today = datetime.today()
        last_friday = today - timedelta(days=today.weekday() + 3)
        return last_friday.strftime('%Y%m%d')



if __name__ == '__main__':
    dailyReport(start='20231222',end='20231229').gen_report()