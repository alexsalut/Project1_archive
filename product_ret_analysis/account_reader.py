#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/12/5 9:11
# @Author  : Suying
# @Site    : 
# @File    : account_reader.py
import time
import pandas as pd
import numpy as np
from record.cats_terminal_reader import CatsFileReader
from record.get_product_terminal import read_terminal_info

from util.file_location import FileLocation


def get_product_record(product, indicator_name, date=None):
    record_path = FileLocation.record_path
    date = time.strftime('%Y%m%d') if date is None else date
    record_df = pd.read_excel(record_path, sheet_name=product, header=0, index_col=0)
    record_df.index = record_df.index.astype(str)
    return float(record_df.loc[date, indicator_name])


def get_monitor_data(indicator_name, date=None):
    date = time.strftime('%Y-%m-%d') if date is None else pd.to_datetime(date).strftime('%Y-%m-%d')
    if indicator_name in ['盼澜1号', '踏浪1号']:
        file_path = rf'{FileLocation.remote_monitor_dir}/monitor_{date}.xlsx'
        col = '科创50指增'
    elif indicator_name == '踏浪3号':
        col = '中证500指增'
        file_path = rf'{FileLocation.remote_monitor_dir}/monitor_zz500_{date}.xlsx'
    else:
        raise KeyError
    monitor_df = pd.read_excel(file_path, sheet_name='monitor目标持仓', header=None, index_col=False)
    value = get_values(monitor_df, col)
    return value


def get_transaction_df(account, account_type, date=None, fee_dict=None):
    date = time.strftime('%Y%m%d') if date is None else date
    product_info = read_terminal_info(date, account)
    if account_type == 'Option':
        df = product_info['期权交易明细']
    else:
        df = product_info['股票交易明细']

    df = df.rename(columns={'证券代码': '代码',
                            '交易': '交易类型',
                            '业务类型': '交易类型',
                            '证券名称': '名称',
                            '成交量': '成交数量',
                            '成交均价': '成交价格',
                            '成交额': '成交金额'
                            })

    if len(df) == 0:
        return df
    else:
        df['代码'] = df['代码'].astype(str).str.split('.', expand=True)[0]
        df['成交金额'] = df.apply(
            lambda x: -abs(x['成交金额']) if '买' in x['交易类型'] else abs(x['成交金额']), axis=1)
        df['成交数量'] = df.apply(
            lambda x: abs(x['成交数量']) if '买' in x['交易类型'] else -abs(x['成交数量']), axis=1)

    if '手续费' in df.columns:
        df['交易费'] = df['手续费']
    elif fee_dict is not None:
        df['交易费'] = df.apply(
            lambda x: abs(x['成交金额'] * fee_dict['卖']) if '卖' in x['交易类型'] else abs(
                x['成交金额'] * fee_dict['买']), axis=1)
    else:
        df['交易费'] = 0
    df['发生金额'] = df['成交金额'] - df['交易费']

    transaction_df = df.groupby('代码').agg(
        {'名称': 'first', '成交金额': 'sum', '成交数量': 'sum', '发生金额': 'sum', '交易费': 'sum'})

    return transaction_df


def get_position_s(account, account_type, date=None):
    date = time.strftime('%Y%m%d') if date is None else date
    account_code = FileLocation.account_code[account]
    if account_type == 'Option':
        account_code = FileLocation.option_account_code[account]
        df = CatsFileReader(file_dir=FileLocation.cats_terminal_dir,
                            account_code=account_code,
                            date=date).read_file([account_type + 'Position'])[account_type + 'Position']

        df['买卖方向'] = df['持仓方向'].apply(lambda x: -1 if x == '义务仓' else 1)
        df['持有数量'] = df['买卖方向'].mul(df['可用数量'])
        df = df.rename(columns={'合约编号': '代码'})
        position_s = df.groupby(['代码'])['持有数量'].sum()
    elif account in ['踏浪1号', '盼澜1号']:
        df = CatsFileReader(file_dir=FileLocation.cats_terminal_dir,
                            account_code=account_code,
                            date=date).read_file([account_type + 'Position'])[account_type + 'Position']

        position_s = df.rename(columns={'当前余额': '持有数量'}).groupby('代码')['持有数量'].sum()
    elif account == '听涟2号':
        position_df = pd.read_csv(
            rf'{FileLocation.emc_terminal_dir}/310310300343_RZRQ_POSITION.{date}.csv',
            encoding='gbk',
            index_col=False).rename(columns={'证券代码': '代码', '持仓数量': '持有数量'})
        position_s = position_df.groupby('代码')['持有数量'].sum()
    elif account == '踏浪3号':
        position_df = pd.read_csv(rf'\\192.168.1.116\trade\broker\qmt_ha\account\Stock\PositionStatics-{date}.csv',
                                  encoding='gbk').query(f'资金账号=={account_code}')
        position_df['证券代码'] = position_df['证券代码'].astype(str).str.zfill(6)
        position_df = position_df.rename(columns={'证券代码': '代码', '当前拥股': '持有数量'})
        position_s = position_df.groupby('代码')['持有数量'].sum()

    else:
        raise KeyError
    return position_s


def get_values(df, indicator):
    loc = np.where(df.apply(lambda x: x.astype(str).str.contains(indicator)))
    return df.iloc[loc[0][0], loc[1][0] + 1]
