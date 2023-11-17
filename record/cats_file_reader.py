#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/8 14:24
# @Author  : Suying
# @Site    : 
# @File    : cats_file_reader.py

import time

import pandas as pd
import rqdatac as rq


class CatsFileReader:
    def __init__(self, file_dir, account_code, date=None):
        self.date = time.strftime('%Y-%m-%d') if date is None else pd.to_datetime(date).strftime('%Y-%m-%d')
        self.file_path_dict = {
            'CreditFund': rf'{file_dir}\CreditFund_{self.date}.csv',
            'CreditPosition': rf'{file_dir}\CreditPosition_{self.date}.csv',
            'StockFund': rf'{file_dir}\StockFund_{self.date}.csv',
            'StockPosition': rf'{file_dir}\StockPosition_{self.date}.csv',
            'Transaction': rf'{file_dir}\TransactionsStatisticsDaily_{self.date}.csv',
        }
        self.account_code = account_code

    def get_cats_account_info(self):
        cats_account = {
            '中信普通账户': self.get_normal_account_info(),
            '中信信用账户': self.get_credit_account_info(),
        }
        return cats_account

    def get_normal_account_info(self):
        normal_file_info = self.read_file(['StockFund', 'StockPosition'])
        cats_normal = gen_info_dict(
            key_list=['账户净资产', '账户证券市值'],
            col_list=['账户资产', '参考市值'],
            df=normal_file_info['StockFund'],
            is_df=True)

        group = group_security(normal_file_info['StockPosition'], 'SymbolFull', inverse=True)
        cats_normal.update({'可转债市值': add_df_cell(group['Convertible'], '参考市值', is_df=True)})
        cats_normal.update({'其他证券市值': sum([add_df_cell(group[key], '参考市值', is_df=True)
                                                 for key in group.keys() if key in (['ETF', 'CS'])])})
        cats_normal.update({'成交额': 0})
        return cats_normal

    def get_credit_account_info(self):
        credit_file_info = self.read_file(['CreditFund', 'CreditPosition'])
        keys = ['账户净资产', '账户总负债', '融资负债', '融券负债', '融资融券费用', '维担比例', '账户证券市值', '现金资产']

        cats_credit = gen_info_dict(
            key_list=keys,
            col_list=['净资产', '负债总额', '融资合约金额', '融券合约金额', ['利息', '费用'], '维护担保比例',
                      '证券市值', '现金资产'],
            df=credit_file_info['CreditFund'],
            is_df=True)

        group = group_security(credit_file_info['CreditPosition'], 'SymbolFull', inverse=True)

        cats_credit.update({'多头证券市值': sum(
            [add_df_cell(group[key], '参考市值', is_df=True) for key in group.keys() if key in (['Convertible', 'CS'])])})
        cats_credit.update({'多头现金类市值': add_df_cell(
                group['ETF'].query('名称 in ["银华日利","短融"]'), '参考市值', is_df=True) + cats_credit['现金资产']})
        cats_credit.update({'可转债市值': add_df_cell(group['Convertible'], '参考市值', is_df=True)})
        cats_credit.update({'成交额': self.get_transaction_vol()})

        return cats_credit

    def get_transaction_vol(self):
        transaction_df = self.read_file(['Transaction'])['Transaction']
        return transaction_df['成交额'].sum()

    def read_file(self, filetype_list):
        data_dict = {}
        for filetype in filetype_list:
            data_dict[filetype] = pd.read_csv(self.file_path_dict[filetype]).query(f'账户=={self.account_code}')

        return data_dict


def group_security(df, ticker_col, inverse=True):
    rq.init()
    if inverse:
        df[ticker_col] = df[ticker_col].apply(lambda x: x.replace('SH', 'XSHG').replace('SZ', 'XSHE'))

    security_type = rq.instruments(df[ticker_col].tolist(), market='cn')
    df['security type'] = [x.type for x in security_type]
    security_type = ['Convertible', 'ETF', 'CS']
    group_dict = {_type: df.query(f'`security type` == "{_type}"')
                  for _type in security_type}
    return group_dict


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
