#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/12/5 9:11
# @Author  : Suying
# @Site    : 
# @File    : account_reader.py
import time
import pandas as pd
import numpy as np
from record.cats_file_reader import CatsFileReader
from util.file_location import FileLocation
def get_product_record(product, indicator_name, date=None):
    record_path = FileLocation.record_path
    date = time.strftime('%Y%m%d') if date is None else date
    record_df = pd.read_excel(record_path, sheet_name=product, header=0, index_col=0)
    record_df.index = record_df.index.astype(str)
    return float(record_df.loc[date, indicator_name])


def get_monitor_data(indicator_name, date=None):
    date = time.strftime('%Y%m%d') if date is None else date
    monitor_df = pd.read_excel(rf'{FileLocation.remote_monitor_dir}/monitor_{date}.xlsx', sheet_name=0, header=None, index_col=False)
    def get_values(df, indicator):
        loc = np.where(monitor_df.apply(lambda x: x.astype(str).str.contains(indicator)))
        return df.iloc[loc[0][0], loc[1][0]+1]
    return get_values(monitor_df, indicator_name)



def get_transaction_df(account, type, date=None):
    date = time.strftime('%Y%m%d') if date is None else date
    if type != 'Option' and account == '听涟2号':
        transaction_df = pd.read_csv(
            rf'{FileLocation.emc_dir}/310310300343_RZRQ_MATCH.{date}.csv',
            index_col=False,
            encoding='gbk'
        ).rename(columns={'证券代码':'代码','信用交易类型': '交易类型'})
    else:
        account_code = FileLocation.account_code[account]
        df = (CatsFileReader(file_dir=FileLocation.cats_dir, account_code=account_code, date=date).get_transaction_df())
        df = df.rename(columns={'证券代码':'代码','交易': '交易类型','成交量':'成交数量','成交均价':'成交价格','成交额': '成交金额'})
        if len(df) > 0:
            df['代码'] = df['代码'].str.split('.', expand=True)[0]
        if type == 'Option':
            transaction_df = df.query('代码.str.startswith("100")', engine='python')
        else:
            transaction_df = df.query('~代码.str.startswith("100")', engine='python')
    transaction_df['成交方向'] = transaction_df['交易类型'].map(lambda x: 1 if '买入' in x else -1)
    transaction_df['成交金额'] = transaction_df['成交金额'].mul(transaction_df['成交方向'])
    transaction_df['成交数量'] = transaction_df['成交数量'].mul(transaction_df['成交方向'])
    new_transaction_df = transaction_df.groupby('代码')[['成交金额', '成交数量']].sum()
    return transaction_df, new_transaction_df




def get_position_s(account, type, date=None):
    date = time.strftime('%Y%m%d') if date is None else date
    account_code = FileLocation.account_code[account]
    if type == 'Option':
        account_code =  FileLocation.option_account_code[account]
        df = CatsFileReader(file_dir=FileLocation.cats_dir, account_code=account_code, date=date).get_trading_position(type+'Position')
        df['买卖方向'] = df['持仓方向'].apply(lambda x: -1 if x=='义务仓' else 1)
        df['持有数量'] = df['买卖方向'].mul(df['可用数量'])
        df = df.rename(columns={'合约编号':'代码'})
        position_s = df.groupby(['代码'])['持有数量'].sum()
    elif account in ['踏浪1号','盼澜1号']:
        df = CatsFileReader(file_dir=FileLocation.cats_dir, account_code=account_code, date=date).get_trading_position(type+'Position')
        position_s = df.rename(columns={'当前余额':'持有数量'}).groupby('代码')['持有数量'].sum()
    elif account == '听涟2号':
        position_df = pd.read_csv(
            rf'{FileLocation.emc_dir}/310310300343_RZRQ_POSITION.{date}.csv',
            encoding='gbk',
            index_col=False).rename(columns={'证券代码':'代码','持仓数量':'持有数量'})
        position_s = position_df.groupby('代码')['持有数量'].sum()
    else:
        raise KeyError
    return position_s





