#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/8 14:24
# @Author  : Suying
# @Site    : 
# @File    : cats_terminal_reader.py

import time
import pandas as pd

from record.account_clearing_reader import update_asset
from util.send_email import Mail, R
from util.utils import get_newest_file, check_file_gen_time, gen_info_dict


class CatsFileReader:
    def __init__(self, file_dir, account_code, date=None):
        self.date = time.strftime('%Y-%m-%d') if date is None else pd.to_datetime(date).strftime('%Y-%m-%d')
        self.file_path_dict = {
            'CreditFund': get_newest_file(file_dir, f'CreditFund_{self.date}*.csv'),
            'CreditPosition': get_newest_file(file_dir, f'CreditPosition_{self.date}*.csv'),
            'StockFund': get_newest_file(file_dir, f'StockFund_{self.date}*.csv'),
            'StockPosition': get_newest_file(file_dir, f'StockPosition_{self.date}*.csv'),
            'Transaction': get_newest_file(file_dir, f'TransactionsStatisticsDaily_{self.date}*.csv'),
            'OptionPosition': get_newest_file(file_dir, f'OptionPosition_{self.date}*.csv'),
            'StockOrder': get_newest_file(file_dir, f'StockOrder_{self.date}*.csv'),
            'OptionFund': get_newest_file(file_dir, f'OptionFund_{self.date}*.csv'),
        }
        self.gen_date_check = check_file_gen_time(path_list=list(self.file_path_dict.values()),
                                                  check_date=self.date)
        self.account_code = account_code
        if self.gen_date_check:
            print(f'读取{self.date}{file_dir}的CATS文件, 生成时间检查通过')
        else:
            Mail().send(
                receivers=R.department['research'],
                subject=f'!!!!{self.date}CATS盘后文件生成时间检查未通过',
                body_content=f'读取盘后{self.date}{file_dir}的CATS文件, 生成时间检查未通过, 请检查CATS文件是否正常生成, 2分钟后重试'
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
        option_file_info = self.read_file(['OptionFund', 'StockOrder'])
        cats_option = gen_info_dict(
            key_list=['账户净资产', '保证金风险度'],
            col_list=['客户总权益', '保证金风险度'],
            df=option_file_info['OptionFund'],
            is_df=True)
        if isinstance(cats_option['保证金风险度'], str):
            cats_option['保证金风险度'] = float(cats_option['保证金风险度'].replace('%', '')) / 100
        cats_option['成交额'] = self.get_transaction(file_type='Option', vol=True)
        cats_option['交易明细'] = self.get_transaction(file_type='Option', vol=False)
        return cats_option

    def get_normal_account_info(self):
        normal_file_info = self.read_file(['StockFund', 'StockPosition', 'StockOrder'])
        cats_normal = gen_info_dict(
            key_list=['账户净资产', '账户证券市值', '资金余额'],
            col_list=['账户资产', '参考市值', '当前余额'],
            df=normal_file_info['StockFund'],
            is_df=True)

        cats_normal['成交额'] = self.get_transaction(file_type='Normal', vol=True)
        cats_normal['交易明细'] = self.get_transaction(file_type='Normal', vol=False)
        if len(normal_file_info['StockPosition']) > 0:
            pos_df = normal_file_info['StockPosition']
            pos_df['SymbolFull'] = pos_df['SymbolFull'].str.split('.', expand=True)[0]
            normal_file_info['StockPosition'] = pos_df

        cats_normal = update_asset(cats_normal,
                                   normal_file_info['StockPosition'],
                                   'SymbolFull',
                                   '名称',
                                   '参考市值')
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
        cats_credit['成交额'] = self.get_transaction(file_type='Credit', vol=True)
        cats_credit['交易明细'] = self.get_transaction(file_type='Credit', vol=False)

        if len(credit_file_info['CreditPosition']) > 0:
            pos_df = credit_file_info['CreditPosition']
            pos_df['SymbolFull'] = pos_df['SymbolFull'].str.split('.', expand=True)[0]
            credit_file_info['CreditPosition'] = pos_df
        cats_credit = update_asset(cats_credit,
                                   credit_file_info['CreditPosition'],
                                   'SymbolFull',
                                   '名称',
                                   '参考市值')
        return cats_credit

    def get_transaction(self, file_type='Normal', vol=False):
        df = self.read_file(['StockOrder'])['StockOrder']
        if file_type == 'Credit':
            order_df = df.query('订单号.str.split("_").str[0].str[-1]=="C"')
        elif file_type == 'Normal':
            order_df = df.query('订单号.str.split("_").str[0].str[-1]=="0"')
        elif file_type == 'Option':
            if len(df) == 0:
                order_df = df
            else:
                order_df = df[df['代码'].astype(str).str.startswith('1000')]
        else:
            raise ValueError('File type is not correct, please input right file type.')
        if vol:
            transaction_vol = order_df['成交额'].sum()
            return transaction_vol
        else:
            return order_df

    def read_file(self, filetype_list):
        data_dict = {}
        for filetype in filetype_list:
            try:
                df = pd.read_csv(self.file_path_dict[filetype], index_col=False)
            except Exception:
                df = pd.read_csv(self.file_path_dict[filetype], index_col=False, encoding='gbk', sep=r'\t')
            data_dict[filetype] = df.query(f'账户=={self.account_code}')
        return data_dict
