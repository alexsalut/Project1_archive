# -*- coding: utf-8 -*-
# @Time    : 2023/7/4 15:27
# @Author  : Youwei Wu
# @File    : account_info.py
# @Software: PyCharm

import time
import os
import pandas as pd

from util.file_location import FileLocation
from record.cats_file_reader import CatsFileReader
from record.matic_file_reader import MaticFileReader


def read_terminal_info(date, account):
    print(f'\n{account}: 获取{date}交易终端导出信息')
    if account in ['踏浪2号', '踏浪3号']:
        info = get_talang23_info(account=account, date=date)
    elif account == '踏浪1号':
        info = get_talang1_info(date=date)
    elif account == '听涟2号':
        info = get_tinglian2_info(date=date)
    elif account == '盼澜1号':
        info = get_panlan1_info(date=date)
    elif account == '弄潮1号':
        info = get_nongchao1_info(date=date)
    elif account == '弄潮2号':
        info = get_nongchao2_info(date=date)
    else:
        raise ValueError('Account name is not correct, please input right account name.')
    print(f'[{account}导出单信息]:\n')
    for key, value in info.items():
        print(f'{key}:{value}\n')
    return info


def get_tinglian2_info(date=None):
    emc_tinglian_dir = FileLocation.account_info_dir_dict['听涟2号 emc']
    cats_tinglian_dir = FileLocation.account_info_dir_dict['听涟2号']
    formatted_date1 = pd.to_datetime(date).strftime("%Y%m%d") if date is not None else time.strftime('%Y%m%d')
    formatted_date2 = pd.to_datetime(date).strftime("%Y-%m-%d") if date is not None else time.strftime('%Y-%m-%d')

    stock_df = pd.read_csv(
        rf'{emc_tinglian_dir}/310310300343_RZRQ_FUND.{formatted_date1}.csv',
        index_col=False,
        encoding='gbk'
    )
    stock_equity = stock_df.loc[0, '资产总值'] - stock_df.loc[0, '总负债']

    cats_option_df = pd.read_csv(
        rf'{cats_tinglian_dir}/OptionFund_{formatted_date2}.csv',
        index_col=False
    ).set_index('账户')  # cats 账户
    cats_option_equity = cats_option_df.loc[FileLocation.option_account_code['听涟2号'], '客户总权益']

    trade_path = rf'{emc_tinglian_dir}/310310300343_RZRQ_MATCH.{formatted_date1}.csv'
    if not os.path.exists(trade_path):
        stock_transaction_vol = 0
    else:
        transaction_df = pd.read_csv(
            trade_path,
            index_col=False,
            encoding='gbk'
        )

        stock_transaction_df = transaction_df.query(
            f'资金账号=={FileLocation.account_code["听涟2号"]}|业务类型.isin(["证券买入", "证券卖出"])')
        stock_transaction_vol = stock_transaction_df['成交数量'].mul(stock_transaction_df['成交价格']).sum()

    option_dir = FileLocation.account_info_dir_dict['听涟2号']
    option_transaction_df = pd.read_csv(rf'{option_dir}/TransactionsStatisticsdaily_{formatted_date2}.csv',
                                        index_col=False).set_index('账户')
    option_code = FileLocation.option_account_code['听涟2号']
    option_transaction_df = option_transaction_df.query(f'账户=={option_code}')

    option_transaction_vol = option_transaction_df.query(
        '证券代码.str.startswith("1000")', engine='python')['成交额'].sum()

    info_dict = {
        '期权权益': cats_option_equity,
        '股票权益': stock_equity,
        '股票市值': stock_df.loc[0, '总市值'],
        '成交额': stock_transaction_vol + option_transaction_vol,
        '股票成交额': stock_transaction_vol,
        '期权成交额': option_transaction_vol,
    }
    return info_dict


def get_talang23_info(account, date=None):
    date = pd.to_datetime(date).strftime('%Y%m%d') if date is not None else pd.to_datetime(time.strftime('%Y%m%d'))
    account_code = FileLocation.account_code[account]
    account_dir = FileLocation.account_info_dir_dict[account]
    info = pd.read_csv(f'{account_dir}/Account-{date}.csv', encoding='gbk').set_index('资金账号').loc[account_code]
    trades = pd.read_csv(f'{account_dir}/Deal-{date}.csv', encoding='gbk')
    account_info_dict = {
        '股票权益': float(info['总资产']),
        '股票市值': info['总市值'],
        '成交额': trades['成交金额'].sum()
    }
    return account_info_dict


def get_talang1_info(date=None):
    panlan_dir = FileLocation.account_info_dir_dict['踏浪1号']
    formatted_date2 = pd.to_datetime(date).strftime("%Y-%m-%d") if date is not None else time.strftime(
        '%Y-%m-%d')
    # stock_normal_s = pd.read_csv(rf'{panlan_dir}/StockFund_{formatted_date2}.csv', index_col=False).set_index(
    #     '账户').loc[FileLocation.account_code['踏浪1号']]

    stock_credit_s = pd.read_csv(rf'{panlan_dir}/CreditFund_{formatted_date2}.csv', index_col=False).set_index(
        '账户').loc[FileLocation.account_code['踏浪1号']]

    option_s = pd.read_csv(rf'{panlan_dir}/OptionFund_{formatted_date2}.csv',
                           index_col=False).set_index(
        '账户').loc[FileLocation.option_account_code['踏浪1号']]

    transaction_df = pd.read_csv(rf'{panlan_dir}/TransactionsStatisticsdaily_{formatted_date2}.csv',
                                 index_col=False).set_index('账户')
    if FileLocation.account_code['踏浪1号'] not in transaction_df.index:
        option_transaction_vol = 0
        stock_transaction_vol = 0
    else:
        transaction_df = transaction_df.loc[FileLocation.account_code['踏浪1号']]
        option_transaction_vol = transaction_df.query('证券代码.str.startswith("1000")', engine='python')[
            '成交额'].sum()
        stock_transaction_vol = transaction_df.query('证券代码.str.len() == 9')['成交额'].sum()

    info_dict = {
        '期权权益': option_s['客户总权益'],
        '股票权益': stock_credit_s['净资产'],
        '股票市值': stock_credit_s['证券市值'],
        '信用账户股票权益': stock_credit_s['净资产'],
        '信用账户股票市值': stock_credit_s['证券市值'],
        '成交额': stock_transaction_vol + option_transaction_vol,
        '股票成交额': stock_transaction_vol,
        '期权成交额': option_transaction_vol,

    }
    return info_dict


def get_panlan1_info(date=None):
    panlan_dir = FileLocation.account_info_dir_dict['盼澜1号']
    formatted_date2 = pd.to_datetime(date).strftime("%Y-%m-%d") if date is not None else time.strftime(
        '%Y-%m-%d')

    stock_credit_s = pd.read_csv(rf'{panlan_dir}/CreditFund_{formatted_date2}.csv', index_col=False).set_index(
        '账户').loc[FileLocation.account_code['盼澜1号']]

    option_s = pd.read_csv(rf'{panlan_dir}/OptionFund_{formatted_date2}.csv',
                           index_col=False).set_index(
        '账户').loc[FileLocation.option_account_code['盼澜1号']]

    transaction_df = pd.read_csv(rf'{panlan_dir}/TransactionsStatisticsdaily_{formatted_date2}.csv',
                                 index_col=False).set_index('账户')
    if FileLocation.account_code['盼澜1号'] not in transaction_df.index:
        option_transaction_vol = 0
        stock_transaction_vol = 0
    else:
        transaction_df = transaction_df.loc[FileLocation.account_code['盼澜1号']]
        option_transaction_vol = transaction_df.query('证券代码.str.startswith("1000")', engine='python')[
            '成交额'].sum()
        stock_transaction_vol = transaction_df.query('证券代码.str.len() == 9')['成交额'].sum()

    info_dict = {
        '期权权益': option_s['客户总权益'],
        '股票权益': stock_credit_s['净资产'],
        '股票市值': stock_credit_s['证券市值'],
        '信用账户股票权益': stock_credit_s['净资产'],
        '信用账户股票市值': stock_credit_s['证券市值'],
        '成交额': option_transaction_vol + stock_transaction_vol,
        '股票成交额': stock_transaction_vol,
        '期权成交额': option_transaction_vol,

    }
    return info_dict


def get_nongchao1_info(date=None):
    account_dict = CatsFileReader(
        file_dir=FileLocation.account_info_dir_dict['弄潮1号 cats'],
        account_code=FileLocation.account_code['弄潮1号 cats'],
        date=date
    ).get_cats_account_info(account_lst=['中信普通账户', '中信信用账户', '中信期权账户'])

    matic_account_dict = MaticFileReader(
        file_dir=FileLocation.account_info_dir_dict['弄潮1号 matic'],
        account_code='衍舟弄潮1号',
        date=date
    ).get_matic_account_info()

    account_dict.update(matic_account_dict)
    return account_dict


def get_nongchao2_info(date=None):
    account_dict = MaticFileReader(
        file_dir=FileLocation.account_info_dir_dict['弄潮2号 matic'],
        account_code='衍舟弄潮2号',
        date=date
    ).get_matic_account_info()
    return account_dict


if __name__ == '__main__':
    get_talang23_info('踏浪3号', date='2024-04-25')
