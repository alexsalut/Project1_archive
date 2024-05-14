#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/3/12 16:34
# @Author  : Suying
# @Site    : 
# @File    : multi_strategy_update.py
import os.path
import time
import shutil
import pandas as pd
import xlwings as xw
from EmQuantAPI import c

from util.utils import fill_in_stock_code, find_index_loc_in_excel

class MultiStrategyPerf:
    def __init__(self, date=None):
        self.date = date if date is not None else time.strftime('%Y%m%d')
        self.account_path = r'\\192.168.1.116\target_position\monitor\多策略超额.xlsx'
        self.zz500_monitor_path = rf'\\192.168.1.116\target_position\monitor\monitor_zz500_{self.date}.xlsx'
        self.kc50_monitor_path = rf'\\192.168.1.116\target_position\monitor\monitor_{self.date}.xlsx'
        date = pd.to_datetime(self.date).strftime('%Y-%m-%d')
        self.zz500_save_path = rf'\\192.168.1.116\target_position\monitor\monitor_zz500_{date}.xlsx'
        self.kc50_save_path = rf'\\192.168.1.116\target_position\monitor\monitor_{date}.xlsx'

    def update(self):
        self.archive_monitor(self.zz500_monitor_path, self.zz500_save_path)
        self.archive_monitor(self.kc50_monitor_path, self.kc50_save_path)
        self.fill_today_perf(sheet_name='多策略超额')
        self.fill_today_perf(sheet_name='CSI500')


    def archive_monitor(self, monitor_path, save_path):
        if not os.path.exists(save_path):
            sheet_dict = self.get_monitor_data(monitor_path)
            app = xw.App(visible=False, add_book=False)
            wb = app.books.open(monitor_path)
            for sheet, data in sheet_dict.items():
                if sheet == 'monitor目标持仓':
                    wb.sheets[sheet].range('C2').value = data
                else:
                    wb.sheets[sheet].range('A1').value = data
                print(f'Archive {sheet} data to {save_path}')
            wb.save(save_path)
            wb.close()
            app.quit()
            app.kill()
            print(f'{save_path} has been archived')
            # if os.path.exists(monitor_path):
            #     os.remove(monitor_path)
            #     print(f'{monitor_path} has been removed')
        else:
            print(f'{self.zz500_save_path} has been archived')



    def fill_today_perf(self, sheet_name):
        info_dict = self.get_perf_data(sheet_name)
        app = xw.App(visible=False, add_book=False)
        print('Generate excel pid:', app.pid)

        wb = app.books.open(self.account_path)
        sheet = wb.sheets[sheet_name]

        row_to_fill = find_index_loc_in_excel(self.account_path, sheet_name, self.date)

        sheet.range(f'A{row_to_fill}').value = self.date
        sheet.range(f'B{row_to_fill}').value = info_dict['策略收益']
        sheet.range(f'C{row_to_fill}').value = info_dict['指数收益']
        sheet.range(f'D{row_to_fill}').formula = f'=B{row_to_fill}-C{row_to_fill}'  # 当日超额
        sheet.range(f'E{row_to_fill}').formula = f'=E{row_to_fill-1}*(1+B{row_to_fill})'  # 多头净值
        sheet.range(f'F{row_to_fill}').formula = f'=F{row_to_fill-1}*(1+C{row_to_fill})'  # 指数净值
        sheet.range(f'G{row_to_fill}').formula = f'=E{row_to_fill}/F{row_to_fill}'  # 累计超额净值
        sheet.range(f'H{row_to_fill}').formula = f'=E{row_to_fill}/F{row_to_fill}-1'  #累计超额
        sheet.range(f'I{row_to_fill}').formula = f'=G{row_to_fill}/MAX(G$2:G{row_to_fill}) - 1'  # 超额回撤
        wb.save(self.account_path)
        try:
            shutil.copy(self.account_path, self.account_path.replace('超额', '超额备份'))
        except Exception as e:
            print(e)
        wb.close()
        app.quit()
        app.kill()
        print(f'Sheet-{sheet_name} has been updated.')



    def get_perf_data(self, sheet_name):
        file_path = self.zz500_save_path if sheet_name == 'CSI500' else self.kc50_save_path
        index = '中证500' if sheet_name == 'CSI500' else '科创50'

        df = pd.read_excel(file_path, sheet_name='monitor目标持仓', index_col=0, header=0, converters={0: str})


        info_dict = {'策略收益': df.loc[f'{index}指增'].iloc[0]}
        info_dict['指数收益'] = df.loc[f'{index}指数'].iloc[1]
        return info_dict

    def get_monitor_data(self, monitor_path):
        f = pd.ExcelFile(monitor_path)
        sheet_names = f.sheet_names
        c.start()
        dict = {}
        for sheet in sheet_names[1:]:
            df = pd.read_excel(monitor_path, sheet_name=sheet, index_col=0, header=0, converters={0: str})
            stock_list = df.index.tolist()
            data = c.css(stock_list, "NAME,SW2021,DIFFERRANGE", f"ClassiFication=1,TradeDate={self.date},ispandas=1")
            data = data.rename(columns={'NAME':'证券名称','SW2021': '申万一级2021','DATES': '更新时间', 'DIFFERRANGE': '涨跌幅%'})
            data = data[['证券名称', '申万一级2021', '更新时间', '涨跌幅%']]
            dict[sheet] = data


        index = '000905.SH' if 'zz500' in monitor_path else '000688.SH'
        index_ret = c.css(
            index,
            "DIFFERRANGE",
            f"TradeDate={self.date}").Data[index][0]/100
        dict['monitor目标持仓'] = index_ret
        c.stop()
        return dict





if __name__ == '__main__':
    MultiStrategyPerf().update()
