#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/3/12 16:34
# @Author  : Suying
# @Site    : 
# @File    : zz500_multi_strategy_update.py
import os.path
import time
import pandas as pd
import xlwings as xw
from EmQuantAPI import c

from util.utils import fill_in_stock_code, find_index_loc_in_excel

class ZZ500MultiStrategyPerf:
    def __init__(self, date=None):
        self.date = date if date is not None else time.strftime('%Y%m%d')
        self.account_path = r'\\192.168.1.116\target_position\monitor\多策略超额.xlsx'
        self.monitor_path = rf'\\192.168.1.116\target_position\monitor\monitor_zz500_{self.date}.xlsx'
        date = pd.to_datetime(self.date).strftime('%Y-%m-%d')
        self.save_path = rf'\\192.168.1.116\target_position\monitor\monitor_zz500_{date}.xlsx'
        self.sheet_name = 'CSI500'

    def update(self):
        self.archive_monitor()
        self.fill_today_perf()


    def archive_monitor(self):
        if not os.path.exists(self.save_path):
            sheet_dict = self.get_monitor_data()
            app = xw.App(visible=False, add_book=False)
            wb = app.books.open(self.monitor_path)
            for sheet, data in sheet_dict.items():
                if sheet == 'monitor目标持仓':
                    wb.sheets[sheet].range('C2').value = data
                else:
                    wb.sheets[sheet].range('A1').value = data
                print(f'Archive {sheet} data to {self.monitor_path}')
            wb.save(self.save_path)
            wb.close()
            app.quit()
            app.kill()
            print(f'{self.save_path} has been archived')
            # if os.path.exists(self.monitor_path):
            #     os.remove(self.monitor_path)
            #     print(f'{self.monitor_path} has been removed')
        else:
            print(f'{self.save_path} has been archived')



    def fill_today_perf(self):
        info_dict = self.get_perf_data()
        app = xw.App(visible=False, add_book=False)
        print('Generate excel pid:', app.pid)

        wb = app.books.open(self.account_path)
        sheet = wb.sheets[self.sheet_name]

        row_to_fill = find_index_loc_in_excel(self.account_path, self.sheet_name, self.date)

        sheet.range(f'A{row_to_fill}').value = self.date
        sheet.range(f'B{row_to_fill}').value = info_dict['策略收益']
        sheet.range(f'C{row_to_fill}').value = info_dict['中证500']
        sheet.range(f'D{row_to_fill}').formula = f'=B{row_to_fill}-C{row_to_fill}'  # 当日超额
        sheet.range(f'E{row_to_fill}').formula = f'=E{row_to_fill-1}*(1+B{row_to_fill})'  # 多头净值
        sheet.range(f'F{row_to_fill}').formula = f'=F{row_to_fill-1}*(1+C{row_to_fill})'  # 指数净值
        sheet.range(f'G{row_to_fill}').formula = f'=E{row_to_fill}/F{row_to_fill}'  # 累计超额净值
        sheet.range(f'H{row_to_fill}').formula = f'=E{row_to_fill}/F{row_to_fill}-1'  #累计超额
        sheet.range(f'I{row_to_fill}').formula = f'=G{row_to_fill}/MAX(G$2:G{row_to_fill}) - 1'  # 超额回撤
        wb.save(self.account_path)
        wb.close()
        app.quit()
        app.kill()
        print(f'Sheet-{self.sheet_name} has been updated.')



    def get_perf_data(self):
        df = pd.read_excel(self.save_path, sheet_name='monitor目标持仓', index_col=0, header=0, converters={0: str})
        info_dict = {'策略收益': df.loc['中证500指增'].iloc[0]}
        info_dict['中证500'] = df.loc['中证500指数'].iloc[1]
        return info_dict

    def get_monitor_data(self):
        f = pd.ExcelFile(self.monitor_path)
        sheet_names = f.sheet_names
        c.start()
        dict = {}
        for sheet in sheet_names[1:]:
            df = pd.read_excel(self.monitor_path, sheet_name=sheet, index_col=0, header=0, converters={0: str})
            stock_list = df.index.tolist()
            data = c.css(stock_list, "NAME,SW2021,DIFFERRANGE", f"ClassiFication=1,TradeDate={self.date},ispandas=1")
            data = data.rename(columns={'NAME':'证券名称','SW2021': '申万一级2021','DATES': '更新时间', 'DIFFERRANGE': '涨跌幅%'})
            data = data[['证券名称', '申万一级2021', '更新时间', '涨跌幅%']]
            dict[sheet] = data

        zz500_index_ret = c.css(
            '000905.SH',
            "DIFFERRANGE",
            f"TradeDate={self.date}").Data['000905.SH'][0]/100
        dict['monitor目标持仓'] = zz500_index_ret
        return dict





if __name__ == '__main__':
    ZZ500MultiStrategyPerf('20240319').update()
