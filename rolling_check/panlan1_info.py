#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/23 16:08
# @Author  : Suying
# @Site    : 
# @File    : panlan1_info.py

import time

import pandas as pd

from util.file_location import FileLocation as FL
from dbfread import DBF


class Panlan1AccountInfo:
    def __init__(self):
        account_dir = FL().account_info_dir_dict['panlan1']
        self.panlan1_today_option_path = rf'{account_dir}/OptionFund.dbf'
        self.panlan1_today_stock_path = rf'{account_dir}/StockFund.dbf'

    def get_panlan1_account_info(self, date=None):
        date = time.strftime('%Y%m%d') if date is None else pd.to_datetime(date).strftime("%Y%m%d")
        if date == time.strftime('%Y%m%d'):
            return self.get_panlan1_today_info()
        else:
            return self.get_panlan1_history_info(date)

    def get_panlan1_history_info(self, date):
        date = pd.to_datetime(date).strftime('%Y-%m-%d')
        account_dir = FL().account_info_dir_dict['panlan1']
        option_s = pd.read_csv(rf'{account_dir}/OptionFund_{date}.csv',
                               index_col=False,
                               dtype={'账户': int, '客户总权益': 'float64', '保证金风险度': str}
                               ).set_index('账户').loc[FL().option_account_code_dict['panlan1']]
        stock_s = pd.read_csv(rf'{account_dir}/StockFund_{date}.csv',
                              dtype={'账户': int, '账户资产': 'float64'},
                              index_col=False).set_index('账户').loc[FL().account_code['panlan1']]
        panlan1_info_dict = {'option equity': option_s['客户总权益'], 'stock equity': stock_s['账户资产'],
                             'margin risk': option_s['保证金风险度']}
        return panlan1_info_dict

    def get_panlan1_today_info(self):
        panlan1_option_s = pd.DataFrame(iter(DBF(self.panlan1_today_option_path))).astype(
            {'ACCT': int, 'TOTEQUITY': 'Float64', 'MARGINRP': str}
        ).set_index('ACCT').loc[FL().option_account_code_dict['panlan1']]
        panlan1_stock_s = pd.DataFrame(iter(DBF(self.panlan1_today_stock_path))).astype(
            {'ACCT': int, 'ASSET': 'Float64'}
        ).set_index('ACCT').loc[FL().account_code['panlan1']]
        panlan1_info_dict = {'option equity': panlan1_option_s['TOTEQUITY'], 'stock equity': panlan1_stock_s['ASSET'],
                             'margin risk': panlan1_option_s['MARGINRP']}
        return panlan1_info_dict
