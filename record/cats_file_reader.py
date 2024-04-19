#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/8 14:24
# @Author  : Suying
# @Site    : 
# @File    : cats_file_reader.py

import time
import os
import glob
import pandas as pd
import datetime
from record.clearing_file_reader import update_asset
from util.send_email import Mail, R


class CatsFileReader:
    def __init__(self, file_dir, account_code, date=None):
        self.date = time.strftime('%Y-%m-%d') if date is None else pd.to_datetime(date).strftime('%Y-%m-%d')
        self.file_path_dict = {
            'CreditFund': self.get_newest_file(file_dir, f'CreditFund_{self.date}.csv'),
            'CreditPosition': self.get_newest_file(file_dir, f'CreditPosition_{self.date}.csv'),
            'StockFund': self.get_newest_file(file_dir, f'StockFund_{self.date}.csv'),
            'StockPosition': self.get_newest_file(file_dir, f'StockPosition_{self.date}.csv'),
            'Transaction': self.get_newest_file(file_dir, f'TransactionsStatisticsDaily_{self.date}.csv'),
            'OptionPosition': self.get_newest_file(file_dir, f'OptionPosition_{self.date}.csv'),
            'StockOrder': self.get_newest_file(file_dir, f'StockOrder_{self.date}.csv'),
            'OptionFund': self.get_newest_file(file_dir, f'OptionFund_{self.date}.csv'),
        }
        self.gen_date_check = self.check_file_gen_time(list(self.file_path_dict.values()))
        self.account_code = account_code
        if self.gen_date_check:
            print(f'读取{self.date}{file_dir}的CATS文件, 生成时间检查通过')
        else:
            Mail().send(
                receivers=R.department['research'],
                subject=f'读取{self.date}{file_dir}的CATS文件, 生成时间检查未通过',
                body_content=f'读取{self.date}{file_dir}的CATS文件, 生成时间检查未通过, 请检查CATS文件是否生成, 2分钟后重试'
            )
            time.sleep(120)
            self.__init__(file_dir, account_code, date)

    def get_cats_account_info(self, account_lst):
        cats_account = {}
        for acc in account_lst:
            if acc == '中信普通账户':
                cats_account[acc] = self.get_normal_account_info()
            elif acc == '中信信用账户':
                cats_account[acc] = self.get_credit_account_info()
            elif acc == '中信期权账户':
                cats_account[acc] = self.get_option_account_info()
            else:
                raise ValueError('Account name is not correct, please input right account name.')

        return cats_account


    def get_option_account_info(self):
        option_file_info = self.read_file(['OptionFund'])
        cats_option = gen_info_dict(
            key_list=['账户净资产', '保证金风险度'],
            col_list=['客户总权益', '保证金风险度'],
            df=option_file_info['OptionFund'],
            is_df=True)
        return cats_option


    def get_normal_account_info(self):
        normal_file_info = self.read_file(['StockFund', 'StockPosition', 'StockOrder'])
        cats_normal = gen_info_dict(
            key_list=['账户净资产', '账户证券市值', '资金余额'],
            col_list=['账户资产', '参考市值', '当前余额'],
            df=normal_file_info['StockFund'],
            is_df=True)

        cats_normal['成交额'] = self.get_transaction_vol(normal_file_info['StockOrder'], file_type='normal')
        num = len(normal_file_info['StockPosition'])
        normal_file_info['StockPosition']['SymbolFull'] = \
        normal_file_info['StockPosition']['SymbolFull'].str.split('.', expand=True)[0] if num >0 else None
        cats_normal = update_asset(cats_normal, normal_file_info['StockPosition'], 'SymbolFull', '名称', '参考市值')

        return cats_normal

    def get_credit_account_info(self):
        credit_file_info = self.read_file(['CreditFund', 'CreditPosition', 'StockOrder'])
        keys = ['账户净资产', '账户总负债', '融资负债', '融券负债', '融资融券费用', '维担比例', '账户证券市值',
                '资金余额']

        cats_credit = gen_info_dict(
            key_list=keys,
            col_list=['净资产', '负债总额', '融资合约金额', '融券合约金额', ['利息', '费用'], '维护担保比例',
                      '证券市值', '现金资产'],
            df=credit_file_info['CreditFund'],
            is_df=True)

        cats_credit['维担比例'] = float(str(cats_credit['维担比例']).replace('%', '')) / 100
        cats_credit['成交额'] = self.get_transaction_vol(credit_file_info['StockOrder'], file_type='credit')

        if len(credit_file_info['CreditPosition']) > 0:

            credit_file_info['CreditPosition']['SymbolFull'] = credit_file_info['CreditPosition']['SymbolFull'].str.split('.', expand=True)[0]
        cats_credit = update_asset(cats_credit, credit_file_info['CreditPosition'], 'SymbolFull', '名称', '参考市值')
        return cats_credit

    def get_trading_position(self, file_type):
        position_df = self.read_file([file_type])[file_type]
        return position_df

    def get_transaction_df(self):
        transaction_df = self.read_file(['Transaction'])['Transaction'].query(f'账户=={self.account_code}')
        return transaction_df


    def get_transaction_vol(self, df, file_type='normal'):
        if self.account_code == 4069336:
            if file_type == 'normal':
                order_df = df.query('订单号.str.startswith("SZHTS0")')
            elif file_type == 'credit':
                order_df = df.query('订单号.str.startswith("SZHTSC")')
            else:
                raise ValueError('File type is not correct, please input right file type.')
        else:
            order_df = df

        transaction_vol = order_df['成交额'].sum()
        return transaction_vol

    def read_file(self, filetype_list):
        data_dict = {}
        for filetype in filetype_list:
            try:
                df = pd.read_csv(self.file_path_dict[filetype], index_col=False)
            except:
                df = pd.read_csv(self.file_path_dict[filetype], index_col=False, encoding='gbk', sep=r'\t')
            data_dict[filetype] = df.query(f'账户=={self.account_code}')
        return data_dict

    def check_file_gen_time(self, path_list):
        for path in path_list:
            gen_time = datetime.datetime.fromtimestamp(os.path.getmtime(path))
            if gen_time < datetime.datetime.strptime(self.date, '%Y-%m-%d').replace(hour=15, minute=0, second=0):
                return False
        return True

    @staticmethod
    def get_newest_file(directory, key):
        file_list = glob.glob(f'{directory}/{key}')
        time_list = [os.path.getmtime(file) for file in file_list]
        newest_file = file_list[time_list.index(max(time_list))]
        return newest_file


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

