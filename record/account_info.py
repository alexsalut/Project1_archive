# -*- coding: utf-8 -*-
# @Time    : 2023/7/4 15:27
# @Author  : Youwei Wu
# @File    : account_info.py
# @Software: PyCharm

import os
import time

import pandas as pd
from file_location import FileLocation as FL
from util.utils import send_email


def read_account_info(date, account):
    if account in ['talang2', 'talang3']:
        return get_talang23_info(account=account, date=date)
    elif account == 'talang1':
        return get_talang1_info(date=date)
    elif account == 'tinglian2':
        return get_tinglian2_info(date=date)
    elif account == 'panlan1':
        return get_panlan1_info(date=date)
    else:
        raise ValueError('account name is not correct, please input right account name')


def get_tinglian2_info(date=None):
    emc_tinglian_dir = FL().account_info_dir_dict['tinglian2 emc']
    cats_tinglian_dir = FL().account_info_dir_dict['tinglian2 cats']
    formatted_date1 = pd.to_datetime(date).strftime("%Y%m%d") if date is not None else time.strftime('%Y%m%d')
    formatted_date2 = pd.to_datetime(date).strftime("%Y-%m-%d") if date is not None else time.strftime('%Y-%m-%d')

    stock_df = pd.read_csv(
        rf'{emc_tinglian_dir}/310310300343_RZRQ_FUND.{formatted_date1}.csv',
        index_col=False,
        encoding='gbk'
    )
    option_df1 = pd.read_csv(
        rf'{emc_tinglian_dir}/310317000090_OPTION_FUND.{formatted_date1}.csv',
        index_col=False,
        encoding='gbk'
    )  # emc 账户
    option_df2 = pd.read_csv(
        rf'{cats_tinglian_dir}/OptionFund_{formatted_date2}.csv',
        index_col=False,
    ).set_index('账户') # cats 账户
    transaction_df = pd.read_csv(
        rf'{emc_tinglian_dir}/310310300343_RZRQ_MATCH.{formatted_date1}.csv',
        index_col=False,
        encoding='gbk'
    ).query(f'资金账号=={FL().stock_account_code_dict["tinglian2"]}')
    info_dict = {
        'cats期权权益': option_df2.loc[FL().option_account_code_dict['tinglian2'], '资金总额'],
        'emc期权权益': option_df1.loc[0, '资产总值'],
        '期权权益': option_df1.loc[0, '资产总值'] + option_df2.loc[FL().option_account_code_dict['tinglian2'], '资金总额'],
        '股票权益': stock_df.loc[0, '资产总值'] - stock_df.loc[0, '总负债'],
        '股票市值': stock_df.loc[0, '总市值'],
        '成交额': transaction_df['成交数量'].mul(transaction_df['成交价格']).sum()
    }
    return info_dict


def get_talang23_info(account, date=None):
    date = pd.to_datetime(date).strftime('%Y%m%d') if date is not None else pd.to_datetime(time.strftime('%Y%m%d'))
    account_code = FL().stock_account_code_dict[account]
    account_dir = FL().account_info_dir_dict[account]
    info = pd.read_csv(f'{account_dir}/Account-{date}.csv', encoding='gbk').set_index('资金账号').loc[account_code]
    trades = pd.read_csv(f'{account_dir}/Deal-{date}.csv', encoding='gbk')
    account_info_dict = {
        '股票权益': float(info['总资产']),
        '股票市值': info['股票总市值'],
        '成交额': trades['成交金额'].sum()
    }
    return account_info_dict


def get_talang1_info(date=None):
    account_dir = FL().account_info_dir_dict['talang1']
    account_code = FL().stock_account_code_dict['talang1']

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
    panlan_dir = FL().account_info_dir_dict['panlan1']
    formatted_date2 = pd.to_datetime(date).strftime("%Y-%m-%d") if date is not None else time.strftime(
        '%Y-%m-%d')
    stock_putong_s = \
        pd.read_csv(rf'{panlan_dir}/StockFund_{formatted_date2}.csv', index_col=False).set_index(
            '账户').loc[
            FL().stock_account_code_dict['panlan1']]

    stock_credit_s = pd.read_csv(rf'{panlan_dir}/CreditFund_{formatted_date2}.csv', index_col=False).set_index(
        '账户').loc[FL().stock_account_code_dict['panlan1']]

    option_s = pd.read_csv(rf'{panlan_dir}/OptionFund_{formatted_date2}.csv', index_col=False).set_index(
                '账户').loc[
                FL().option_account_code_dict['panlan1']]

    transaction_df = pd.read_csv(rf'{panlan_dir}/TransactionsStatisticsDaily_{formatted_date2}.csv',
                        index_col=False).set_index(
                '账户').loc[FL().stock_account_code_dict['panlan1']]

    info_dict = {
        '期权权益': option_s['客户总权益'],
        '股票权益': stock_putong_s['账户资产'] + stock_credit_s['净资产'],
        '股票市值': stock_putong_s['证券市值'] + stock_credit_s['证券市值'],
        '普通账户股票权益': stock_putong_s['账户资产'],
        '普通账户股票市值': stock_putong_s['证券市值'],
        '信用账户股票权益': stock_credit_s['净资产'],
        '信用账户股票市值': stock_credit_s['证券市值'],
        '成交额': transaction_df['成交额'].sum()
    }
    return info_dict


if __name__ == '__main__':
    read_account_info(date='20231030',account='panlan1')
