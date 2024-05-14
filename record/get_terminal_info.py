# -*- coding: utf-8 -*-
# @Time    : 2023/7/4 15:27
# @Author  : Youwei Wu
# @File    : get_terminal_info.py
# @Software: PyCharm

import time
import os
import pandas as pd

from util.file_location import FileLocation
from record.cats_terminal_reader import CatsFileReader
from record.matic_terminal_reader import MaticFileReader
from record.terminal_file_reader import read_terminal_file

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
    elif account == '听涟1号':
        info = get_tinglian1_info(date=date)
    else:
        raise ValueError('Account name is not correct, please input right account name.')
    print(f'[{account}导出单信息]:\n')
    for key, value in info.items():
        print(f'{key}:{value}\n')
    return info


def get_tinglian1_info(date=None):
    date = pd.to_datetime(date).strftime('%Y%m%d') if date is not None else time.strftime('%Y%m%d')
    dz_dir = FileLocation.account_info_dir_dict['听涟1号 dz']
    dz_info = read_terminal_file(dz_dir, '东证期货账户', date=date)
    cd_code = FileLocation.account_code['听涟1号']
    cd_dir = FileLocation.account_info_dir_dict['听涟1号 cd']
    cd_info = read_terminal_file(cd_dir, '财达普通账户', cd_code, date)

    info_dict = {
        '股票权益': cd_info['账户净资产'],
        '股票市值': cd_info['证券市值'],
        '股票成交额': cd_info['成交额'],
        '期货权益': dz_info['账户净资产'],
        '期货市值': dz_info['证券市值']
    }
    return info_dict


def get_tinglian2_info(date=None):
    emc_tinglian_dir = FileLocation.account_info_dir_dict['听涟2号 emc']
    emc_account_code = FileLocation.account_code["听涟2号"]
    cats_tinglian_dir = FileLocation.account_info_dir_dict['听涟2号']
    cats_option_code = FileLocation.option_account_code['听涟2号']
    emc_info = read_terminal_file(emc_tinglian_dir, '东财信用账户', emc_account_code, date)
    cats_option_info = read_terminal_file(cats_tinglian_dir, '中信期权账户', FileLocation.option_account_code['听涟2号'], date)

    c = CatsFileReader(cats_tinglian_dir, cats_option_code, date)
    option_transaction_vol = c.get_transaction_info().query('证券代码.str.startswith("1000")', engine='python')['成交额'].sum()

    info_dict = {
        '期权权益': cats_option_info['账户净资产'],
        '股票权益': emc_info['账户净资产'],
        '股票市值': emc_info['证券市值'],
        '成交额': emc_info['成交额'] + option_transaction_vol,
        '股票成交额': emc_info['成交额'],
        '期权成交额': option_transaction_vol,
    }
    return info_dict


def get_talang23_info(account, date=None):
    date = pd.to_datetime(date).strftime('%Y%m%d') if date is not None else time.strftime('%Y%m%d')
    account_code = FileLocation.account_code[account]
    account_dir = FileLocation.account_info_dir_dict[account]
    account_info = read_terminal_file(account_dir, '华安普通账户', account_code, date)
    return account_info


def get_talang1_info(date=None):
    dir = FileLocation.account_info_dir_dict['踏浪1号']
    stock_account_code = FileLocation.account_code['踏浪1号']
    option_account_code = FileLocation.option_account_code['踏浪1号']
    stock_info = read_terminal_file(dir, '中信信用账户', stock_account_code, date)
    option_info = read_terminal_file(dir, '中信期权账户', option_account_code, date)
    transaction_df = CatsFileReader(dir, stock_account_code, date).get_transaction_info()
    option_transaction_vol = transaction_df.query('证券代码.str.startswith("1000")', engine='python')[
            '成交额'].sum()
    stock_transaction_vol = transaction_df.query('证券代码.str.len() == 9')['成交额'].sum()

    info_dict = {
        '期权权益': option_info['账户净资产'],
        '股票权益': stock_info['账户净资产'],
        '股票市值': stock_info['账户证券市值'],
        '信用账户股票权益': stock_info['账户净资产'],
        '信用账户股票市值': stock_info['账户证券市值'],
        '成交额': stock_transaction_vol + option_transaction_vol,
        '股票成交额': stock_transaction_vol,
        '期权成交额': option_transaction_vol,

    }
    return info_dict


def get_panlan1_info(date=None):
    dir = FileLocation.account_info_dir_dict['盼澜1号']
    stock_account_code = FileLocation.account_code['盼澜1号']
    option_account_code = FileLocation.option_account_code['盼澜1号']
    stock_info = read_terminal_file(dir, '中信信用账户', stock_account_code, date)
    option_info = read_terminal_file(dir, '中信期权账户', option_account_code, date)
    transaction_df = CatsFileReader(dir, stock_account_code, date).get_transaction_info()
    option_transaction_vol = transaction_df.query('证券代码.str.startswith("1000")', engine='python')[
            '成交额'].sum()
    stock_transaction_vol = transaction_df.query('证券代码.str.len() == 9')['成交额'].sum()

    info_dict = {
        '期权权益': option_info['账户净资产'],
        '股票权益': stock_info['账户净资产'],
        '股票市值': stock_info['账户证券市值'],
        '信用账户股票权益': stock_info['账户净资产'],
        '信用账户股票市值': stock_info['账户证券市值'],
        '成交额': stock_transaction_vol + option_transaction_vol,
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
    read_terminal_info('20240509','听涟1号')
