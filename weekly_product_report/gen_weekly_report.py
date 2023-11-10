#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/10 15:58
# @Author  : Suying
# @Site    : 
# @File    : gen_weekly_report.py

import pandas as pd
import xlwings as xw
from datetime import datetime, timedelta
from weekly_product_report.gen_stats import ProductStats


class WeeklyReport:
    def __init__(self, end=None):
        self.dir = r'C:\Users\Yz02\Desktop\产品每周汇总'
        self.end = end if end is not None else self.get_last_friday()
        self.start = (pd.to_datetime(self.end) - timedelta(days=7)).strftime('%Y%m%d')
        self.report_path = rf'{self.dir}\\衍舟业绩周报_{self.end}.xlsx'
        self.last_report_path = rf'{self.dir}\\衍舟业绩周报_{self.start}.xlsx'
        self.stats = ProductStats(end=self.end).get_all_stats()

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
        self.copy_last_file()

        self.gen_seperate_report(sheet_name='公开版')
        self.gen_seperate_report(sheet_name='内部版')


    def copy_last_file(self):
        app = xw.App(visible=False, add_book=False)
        wb = app.books.open(self.last_report_path)
        wb.save(self.report_path)
        wb.close()
        app.quit()
        print(f'Copy {self.last_report_path} to {self.report_path} successfully')

    def gen_seperate_report(self, sheet_name='公开版'):
        app = xw.App(visible=False, add_book=False)
        wb = app.books.open(self.report_path)
        sheet = wb.sheets[sheet_name]
        product_index_dict = self.public_index_dict if sheet_name == '公开版' else self.private_index_dict
        sheet.range('B1').value = f'业绩周报【{self.start[:4]}年{self.start[4:6]}月{self.start[6:]}日-{self.end[:4]}年{self.end[4:6]}月{self.end[6:]}日】'



        for product in product_index_dict.keys():
            product_index = product_index_dict[product]
            product_cols = self.enhance_cols if product in self.product_type_dict['指增'] else self.hedge_cols
            self.input_product_stats(sheet, product_index, product_cols, self.stats[product])

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
