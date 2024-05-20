#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/8 14:43
# @Author  : Suying
# @Site    : 
# @File    : matic_terminal_reader.py

import time
import pandas as pd

from record.account_clearing_reader import update_asset
from record.cats_terminal_reader import gen_info_dict
from util.utils import get_newest_file, check_file_gen_time


class MaticFileReader:
    def __init__(self, file_dir, account_code, date=None):
        self.date = time.strftime('%Y%m%d') if date is None else pd.to_datetime(date).strftime('%Y%m%d')
        self.file_dir = file_dir
        self.file_path_dict = {
            '信用成交': get_newest_file(self.file_dir, f'信用交易_成交报表_{self.date}'),
            '信用持仓': get_newest_file(self.file_dir, f'信用交易_持仓报表_{self.date}'),
            '信用资产': get_newest_file(self.file_dir, f'信用交易_资产报表_{self.date}'),
            '普通成交': get_newest_file(self.file_dir, f'普通交易_成交报表_{self.date}'),
            '普通持仓': get_newest_file(self.file_dir, f'普通交易_持仓报表_{self.date}'),
            '普通资产': get_newest_file(self.file_dir, f'普通交易_资产报表_{self.date}'),
        }
        self.gen_date_check = check_file_gen_time(list(self.file_path_dict.values()), self.date, 15)
        self.account_code = account_code
        if self.gen_date_check:
            print(f'读取{self.date}{file_dir}的MATIC文件, 生成时间检查通过')
        else:
            raise ValueError(f'读取{self.date}{file_dir}的MATIC文件, 生成时间检查未通过')

    def get_matic_account_info(self):
        matic_account = {
            '华泰普通账户': self.get_normal_account_info(),
            '华泰信用账户': self.get_credit_account_info(),
            '华泰期货账户': self.get_future_account_info(),
        }
        return matic_account

    def get_credit_account_info(self):
        credit = self.read_file(['信用资产', '信用持仓', '信用成交'])
        credit_asset = gen_info_dict(
            key_list=['账户净资产', '账户总负债', '融资负债', '融券负债', '融资融券费用', '维担比例', '账户证券市值',
                      '资金余额'],
            col_list=['净资产', '合约总负债', '融资市值', '融券市值', ['利息', '费用'], '维持担保比例',
                      '证券市值', '现金资产'],
            df=credit['信用资产'],
            is_df=True)

        credit_asset.update({'成交额': credit['信用成交']['成交金额'].sum()})
        credit['信用持仓']['证券代码'] = credit['信用持仓']['证券代码'].astype(str)
        credit_asset = update_asset(credit_asset, credit['信用持仓'], '证券代码', '证券名称', '市值（CNY）')
        return credit_asset

    def get_normal_account_info(self):
        normal = self.read_file(['普通资产', '普通持仓', '普通成交'])
        normal_asset = gen_info_dict(
            key_list=['账户净资产', '账户证券市值', '资金余额', '成交额'],
            col_list=['总资产', '证券市值', '可用资金', '总成交金额'],
            df=normal['普通资产'],
            is_df=True)
        normal['普通持仓']['证券代码'] = normal['普通持仓']['证券代码'].astype(str)
        normal_asset = update_asset(normal_asset, normal['普通持仓'], '证券代码', '证券名称', '市值（CNY）')
        return normal_asset

    @staticmethod
    def get_future_account_info():
        future_asset = ['账户净资产', '多头期权市值', '空头期权市值', '保证金风险度']
        future_dict = {key: 0 for key in future_asset}
        return future_dict

    def read_file(self, filetype_list):
        data_dict = {}
        for filetype in filetype_list:
            data_dict[filetype] = pd.read_csv(self.file_path_dict[filetype], encoding='gbk').query(
                f'账户名称=="{self.account_code}"')

        return data_dict
