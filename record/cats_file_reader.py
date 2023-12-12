#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/8 14:24
# @Author  : Suying
# @Site    : 
# @File    : cats_file_reader.py

import time

import pandas as pd
import rqdatac as rq
from util.clearing_file_reader import update_asset

class CatsFileReader:
    def __init__(self, file_dir, account_code, date=None):
        self.date = time.strftime('%Y-%m-%d') if date is None else pd.to_datetime(date).strftime('%Y-%m-%d')
        self.file_path_dict = {
            'CreditFund': rf'{file_dir}\CreditFund_{self.date}.csv',
            'CreditPosition': rf'{file_dir}\CreditPosition_{self.date}.csv',
            'StockFund': rf'{file_dir}\StockFund_{self.date}.csv',
            'StockPosition': rf'{file_dir}\StockPosition_{self.date}.csv',
            'Transaction': rf'{file_dir}\TransactionsStatisticsDaily_{self.date}.csv',
            'OptionPosition': rf'{file_dir}\OptionPosition_{self.date}.csv',
            'StockOrder': rf'{file_dir}\StockOrder_{self.date}.csv',
        }
        self.account_code = account_code

    def get_cats_account_info(self):
        cats_account = {
            '中信普通账户': self.get_normal_account_info(),
            '中信信用账户': self.get_credit_account_info(),
        }
        return cats_account

    def get_normal_account_info(self):
        normal_file_info = self.read_file(['StockFund', 'StockPosition','StockOrder'])
        cats_normal = gen_info_dict(
            key_list=['账户净资产', '账户证券市值','资金余额'],
            col_list=['账户资产', '参考市值','当前余额'],
            df=normal_file_info['StockFund'],
            is_df=True)

        cats_normal['成交额'] = self.get_transaction_vol(normal_file_info['StockOrder'], type='normal')
        normal_file_info['StockPosition']['SymbolFull'] = normal_file_info['StockPosition']['SymbolFull'].str.split('.',expand=True)[0]
        cats_normal = update_asset(cats_normal, normal_file_info['StockPosition'], 'SymbolFull', '名称', '参考市值')

        return cats_normal

    def get_credit_account_info(self):
        credit_file_info = self.read_file(['CreditFund', 'CreditPosition','StockOrder'])
        keys = ['账户净资产', '账户总负债', '融资负债', '融券负债', '融资融券费用', '维担比例', '账户证券市值',
                '资金余额']

        cats_credit = gen_info_dict(
            key_list=keys,
            col_list=['净资产', '负债总额', '融资合约金额', '融券合约金额', ['利息', '费用'], '维护担保比例',
                      '证券市值', '现金资产'],
            df=credit_file_info['CreditFund'],
            is_df=True)

        cats_credit['维担比例'] = float(cats_credit['维担比例'].replace('%',''))/100
        cats_credit['成交额'] = self.get_transaction_vol(credit_file_info['StockOrder'], type='credit')

        credit_file_info['CreditPosition']['SymbolFull'] = credit_file_info['CreditPosition']['SymbolFull'].str.split('.',expand=True)[0]
        cats_credit = update_asset(cats_credit, credit_file_info['CreditPosition'], 'SymbolFull', '名称', '参考市值')
        return cats_credit



    def get_trading_position(self, file_type):
        position_df = self.read_file([file_type])[file_type].query(f'账户=={self.account_code}')
        return position_df

    def get_transaction_df(self):
        transaction_df = self.read_file(['Transaction'])['Transaction'].query(f'账户=={self.account_code}')
        return transaction_df

    def get_transaction_vol(self,df, type='normal'):
        if type == 'normal':
            order_df = df.query('订单号.str.startswith("SZHTS0")')
        elif type == 'credit':
            order_df = df.query('订单号.str.startswith("SZHTSC")')
        else:
            raise ValueError('成交额计算错误, 交易价格为NaN，请检查持仓文件')

        transaction_vol = order_df['成交额'].sum()
        return transaction_vol

    def read_file(self, filetype_list):
        data_dict = {}
        for filetype in filetype_list:
            data_dict[filetype] = pd.read_csv(self.file_path_dict[filetype]).query(f'账户=={self.account_code}')

        return data_dict



def add_df_cell(df, col_list, is_df=False):
    if isinstance(col_list, str):
        col_list = [col_list]

    if is_df:
        selected_col = [col for col in df.columns for p in col_list if p in col]
        return df[selected_col].sum(axis=1).sum()
    else:
        selected_col = [col for col in df.index for p in col_list if p in col]
        return df[selected_col].sum()


def gen_info_dict(df, key_list, col_list, is_df=False):
    info_dict = {
        key: add_df_cell(df, col, is_df=is_df) for key, col in list(zip(key_list, col_list))
    }
    return info_dict
