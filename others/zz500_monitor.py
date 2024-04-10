#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/3/11 11:00
# @Author  : Suying
# @Site    : 
# @File    : zz500_monitor.py
import os.path

import numpy as np
import pandas as pd
import rqdatac as rq
import xlwings as xw

from util.utils import retry_save_excel, fill_in_stock_code

def update_zz500_next_trading_day_pos(date=None):
    date = date if date is not None else pd.Timestamp.now().strftime('%Y%m%d')
    next_trading_day = rq.get_next_trading_date(date, 1).strftime('%Y%m%d')
    next_monitor_path = rf'\\192.168.1.116\target_position\monitor\monitor_zz500_{next_trading_day}.xlsx'
    template_path = r'\\192.168.1.116\target_position\monitor\monitor_zz500_template.xlsx'
    print(f'更新{date}的中证500持仓监控表')
    if not os.path.exists(next_monitor_path):
        app = xw.App(visible=False, add_book=False)
        print('Generate excel pid:', app.pid)
        app.display_alerts = False
        app.screen_updating = False
        print('open template')
        wb = app.books.open(template_path)
        wb.save(next_monitor_path)
        wb.close()
        app.quit()
        app.kill()
        print(f'{next_monitor_path} copied from template')

        strategy_pos = read_pos_file(date)
        app = xw.App(visible=False, add_book=False)
        print('Generate excel pid:', app.pid)
        app.display_alerts = False
        app.screen_updating = False
        wb = app.books.open(next_monitor_path)

        sheet = wb.sheets['monitor目标持仓']
        sheet.range('B1').value = next_trading_day

        for strategy, pos in strategy_pos.items():
            strategy_name = strategy.replace('zz500_', '')
            sheet = wb.sheets[strategy_name]
            clear_previous_rows(sheet)
            pos_reshaped = np.reshape(pos, (-1, 1))

            sheet.range(f'A2:A{1+len(pos)}').value = pos_reshaped
            print(f'{strategy_name} updated')
        retry_save_excel(wb=wb, file_path=next_monitor_path)
        wb.close()
        app.quit()
        app.kill()
        print('*' * 25, 'Next Monitor Updated')

        check_pos_correct(next_trading_day, strategy_pos, next_monitor_path)


def clear_previous_rows(sheet):
    row2 = 2
    rows_to_delete = range(row2, 180)
    for row in rows_to_delete:
        sheet.range(f'A{row}').value = None

def read_pos_file(date):
    path = rf'\\192.168.1.116\target_position\summary_zz500\tag_pos_{date}.csv'
    pos_s = pd.read_csv(path, index_col=0, converters={'ticker': str})['strategy']
    strategy_lst = pos_s.unique().tolist()
    pos_dict = {
        strategy: fill_in_stock_code([stock.zfill(6) for stock in pos_s[pos_s == strategy].index.tolist()])
        for strategy in strategy_lst
    }
    return pos_dict


def check_pos_correct(date, pos_dict, monitor_path):
    sep = '-' * 25
    print(f'{sep}检查{date}的中证500持仓监控表{sep}')
    error_lst = []
    for strategy, pos in pos_dict.items():
        strategy_name = strategy.replace('zz500_', '')
        df = pd.read_excel(monitor_path,
                           sheet_name=strategy_name,
                           converters={'ticker': str},
                           index_col=0)
        pos_list = df.index.tolist()
        if pos_list != pos:
            error_lst.append(strategy_name)
    monitor_date = pd.read_excel(monitor_path, sheet_name='monitor目标持仓', index_col=0, header=None).iloc[0, 0]
    if str(monitor_date) != date:
        error_lst.append('日期')
    if len(error_lst) == 0:
        print('Next Monitor is correctly updated.')
    else:
        raise ValueError(f'Next Monitor is not correctly updated, please check {error_lst}')





if __name__ == '__main__':
    update_zz500_next_trading_day_pos()

