# -*- coding: utf-8 -*-
# @Time    : 2023/7/4 15:27
# @Author  : Youwei Wu
# @File    : account.py
# @Software: PyCharm

import os
import time

import pandas as pd


def read_account_info(date, account):
    if account == 'tanglang3':
        key = 'iQuant'
    elif account == 'tanglang2':
        key = 'qmt_gf'
    else:
        raise

    os.chdir(rf'\\192.168.1.116\trade\broker\{key}\account\Stock')
    try:
        info = pd.read_csv(f'Account-{date}.csv', encoding='gbk').loc[0]
        trades = pd.read_csv(f'Deal-{date}.csv', encoding='gbk')
    except Exception as e:
        print(e)
        print(f'Account-{date}.csv or Deal-{date}.csv access failed, retry in 20 seconds')
        time.sleep(20)
        read_account_info(date=date, account=account)

    account_info_s = pd.Series({
        '账户':account,
        '交易日': date,
        '总资产': info['总资产'],
        '股票总市值': info['股票总市值'],
        '成交额': trades['成交金额'].sum()
    })
    print(account_info_s)
    return account_info_s



if __name__ == '__main__':
    read_account_info(date='20230911', account='tanglang2')
    read_account_info(date='20230911', account='tanglang3')






