# -*- coding: utf-8 -*-
# @Time    : 2023/7/4 15:27
# @Author  : Youwei Wu
# @File    : account_info.py
# @Software: PyCharm

import os
import time
import glob
import pandas as pd
from file_location import FileLocation as FL
from record.cats_file_reader import CatsFileReader, group_security
from record.matic_file_reader import MaticFileReader


def read_account_info(date, account):
    print(f'{date}获取导出单信息：', account)
    if account in ['talang2', 'talang3']:
        info = get_talang23_info(account=account, date=date)
    elif account == 'talang1':
        info = get_talang1_info(date=date)
    elif account == 'tinglian2':
        info = get_tinglian2_info(date=date)
    elif account == 'panlan1':
        info = get_panlan1_info(date=date)
    elif account == 'nongchao1':
        info = get_nongchao1_info(date=date)
    elif account == 'nongchao2':
        info = get_nongchao2_info(date=date)
    else:
        raise ValueError('account name is not correct, please input right account name')

    print(f'{date}获取导出单信息完成：', account,'\n', info)
    return info


def get_tinglian2_info(date=None):
    emc_tinglian_dir = FL.account_info_dir_dict['tinglian2 emc']
    cats_tinglian_dir = FL.account_info_dir_dict['tinglian2 cats']
    formatted_date1 = pd.to_datetime(date).strftime("%Y%m%d") if date is not None else time.strftime('%Y%m%d')
    formatted_date2 = pd.to_datetime(date).strftime("%Y-%m-%d") if date is not None else time.strftime('%Y-%m-%d')

    stock_df = pd.read_csv(
        rf'{emc_tinglian_dir}/310310300343_RZRQ_FUND.{formatted_date1}.csv',
        index_col=False,
        encoding='gbk'
    )
    stock_equity = stock_df.loc[0, '资产总值'] - stock_df.loc[0, '总负债']

    emc_option_df = pd.read_csv(
        rf'{emc_tinglian_dir}/310317000090_OPTION_FUND.{formatted_date1}.csv',
        index_col=False,
        encoding='gbk'
    )  # emc 账户
    emc_option_equity = emc_option_df.loc[0, '资产总值']

    cats_option_df = pd.read_csv(
        rf'{cats_tinglian_dir}/OptionFund_{formatted_date2}.csv',
        index_col=False,
    ).set_index('账户')  # cats 账户
    cats_option_equity = cats_option_df.loc[FL.option_account_code_dict['tinglian2'], '资金总额']

    transaction_df = pd.read_csv(
        rf'{emc_tinglian_dir}/310310300343_RZRQ_MATCH.{formatted_date1}.csv',
        index_col=False,
        encoding='gbk'
    )

    stock_transaction_df = transaction_df.query(
        f'资金账号=={FL.account_code["tinglian2"]}|业务类型.isin(["证券买入", "证券卖出"])')
    stock_transaction_vol = stock_transaction_df['成交数量'].mul(stock_transaction_df['成交价格']).sum()

    option_dir = FL.account_info_dir_dict['tinglian2 cats']
    option_transaction_df = pd.read_csv(rf'{option_dir}/TransactionsStatisticsDaily_{formatted_date2}.csv',
                                        index_col=False).set_index(
        '账户')
    option_code = FL.option_account_code_dict['tinglian2']
    option_transaction_df = option_transaction_df.query(f'账户=={option_code}')

    option_transaction_vol = option_transaction_df.query('证券代码.str.startswith("1000")', engine='python')[
        '成交额'].sum()

    info_dict = {
        'cats期权权益': cats_option_equity,
        'emc期权权益': emc_option_equity,
        '期权权益': cats_option_equity + emc_option_equity,
        '股票权益': stock_equity,
        '股票市值': stock_df.loc[0, '总市值'],
        '成交额': stock_transaction_vol + option_transaction_vol,
        '股票成交额': stock_transaction_vol,
        '期权成交额': option_transaction_vol,
    }
    return info_dict


def get_talang23_info(account, date=None):
    date = pd.to_datetime(date).strftime('%Y%m%d') if date is not None else pd.to_datetime(time.strftime('%Y%m%d'))
    account_code = FL.account_code[account]
    account_dir = FL.account_info_dir_dict[account]
    info = pd.read_csv(f'{account_dir}/Account-{date}.csv', encoding='gbk').set_index('资金账号').loc[account_code]
    trades = pd.read_csv(f'{account_dir}/Deal-{date}.csv', encoding='gbk')
    account_info_dict = {
        '股票权益': float(info['总资产']),
        '股票市值': info['股票总市值'],
        '成交额': trades['成交金额'].sum()
    }
    return account_info_dict


def get_talang1_info(date=None):
    account_dir = FL.account_info_dir_dict['talang1']
    account_code = FL.account_code['talang1']

    formatted_date = pd.to_datetime(date).strftime("%Y-%m-%d") if date is not None else time.strftime('%Y-%m-%d')
    stock_ordinary = \
        pd.read_csv(rf'{account_dir}/StockFund_{formatted_date}.csv', index_col=False).set_index('账户').loc[
            account_code]
    stock_credit = \
        pd.read_csv(rf'{account_dir}/CreditFund_{formatted_date}.csv', index_col=False).set_index('账户').loc[
            account_code]
    trades = pd.read_csv(rf'{account_dir}/TransactionsStatisticsDaily_{formatted_date}.csv',
                         index_col=False).set_index(
        '账户').loc[account_code]
    account_info_dict = {
        '股票权益': stock_ordinary['账户资产'] + stock_credit['净资产'],
        '股票市值': stock_ordinary['证券市值'] + stock_credit['证券市值'],
        '普通账户股票权益': stock_ordinary['账户资产'],
        '普通账户股票市值': stock_ordinary['证券市值'],
        '信用账户股票权益': stock_credit['净资产'],
        '信用账户股票市值': stock_credit['证券市值'],
        '成交额': trades['成交额'].sum()
    }
    return account_info_dict


def get_panlan1_info(date=None):
    panlan_dir = FL.account_info_dir_dict['panlan1']
    formatted_date2 = pd.to_datetime(date).strftime("%Y-%m-%d") if date is not None else time.strftime(
        '%Y-%m-%d')
    stock_normal_s = \
        pd.read_csv(rf'{panlan_dir}/StockFund_{formatted_date2}.csv', index_col=False).set_index(
            '账户').loc[
            FL.account_code['panlan1']]

    stock_credit_s = pd.read_csv(rf'{panlan_dir}/CreditFund_{formatted_date2}.csv', index_col=False).set_index(
        '账户').loc[FL.account_code['panlan1']]

    option_s = pd.read_csv(rf'{panlan_dir}/OptionFund_{formatted_date2}.csv', index_col=False).set_index(
        '账户').loc[
        FL.option_account_code_dict['panlan1']]

    transaction_df = pd.read_csv(rf'{panlan_dir}/TransactionsStatisticsDaily_{formatted_date2}.csv',
                                 index_col=False).set_index(
        '账户').loc[FL.account_code['panlan1']]

    option_transaction_vol = transaction_df.query('证券代码.str.startswith("1000")', engine='python')['成交额'].sum()
    stock_transaction_vol = transaction_df.query('证券代码.str.len() == 9')['成交额'].sum()

    info_dict = {
        '期权权益': option_s['资金总额'],
        '股票权益': stock_normal_s['账户资产'] + stock_credit_s['净资产'],
        '股票市值': stock_normal_s['证券市值'] + stock_credit_s['证券市值'],
        '普通账户股票权益': stock_normal_s['账户资产'],
        '普通账户股票市值': stock_normal_s['证券市值'],
        '信用账户股票权益': stock_credit_s['净资产'],
        '信用账户股票市值': stock_credit_s['证券市值'],
        '成交额': option_transaction_vol + stock_transaction_vol,
        '股票成交额': stock_transaction_vol,
        '期权成交额': option_transaction_vol,

    }
    return info_dict


def get_nongchao1_info(date=None):
    account_dict = CatsFileReader(
        file_dir=FL.account_info_dir_dict['nongchao1 cats'],
        account_code=FL.account_code['nongchao1 cats'],
        date=date
    ).get_cats_account_info()

    matic_normal_dict = MaticFileReader(
        file_dir=FL.account_info_dir_dict['nongchao1 matic'],
        account_code='衍舟弄潮1号',
        date=date
    ).get_normal_account_info()

    account_dict.update({'华泰普通账户': matic_normal_dict})
    return account_dict


def get_nongchao2_info(date=None):
    account_dict = MaticFileReader(
        file_dir=FL.account_info_dir_dict['nongchao2 matic'],
        account_code='衍舟弄潮2号',
        date=date
    ).get_matic_account_info()
    return account_dict


if __name__ == '__main__':
    read_account_info(date='20231108', account='nongchao1')
