# -*- coding: utf-8 -*-
# @Time    : 2023/7/4 15:27
# @Author  : Youwei Wu
# @File    : account.py
# @Software: PyCharm

import os

import pandas as pd


def read_account_info(date, account):
    if account == 'tanglang3':
        key = 'iQuant'
    elif account == 'tanglang2':
        key = 'qmt_gf'
    else:
        raise

    os.chdir(rf'\\192.168.1.116\trade\broker\{key}\account\Stock')
    info = pd.read_csv(f'Account-{date}.csv', encoding='gbk').loc[0]
    trades = pd.read_csv(f'Deal-{date}.csv', encoding='gbk')

    print(f"\n账户： {account}")
    print(f"交易日： {info['交易日']}")
    print(f"总资产： {info['总资产']}")
    print(f"总市值： {info['股票总市值']}")
    print(f"成交额： {trades['成交金额'].sum()}")


if __name__ == '__main__':
    import time
    today = time.strftime('%Y%m%d')
    read_account_info(date=today, account='tanglang3')
    read_account_info(date=today, account='tanglang2')
