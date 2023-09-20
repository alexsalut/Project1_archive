# -*- coding: utf-8 -*-
# @Time    : 2023/7/4 15:27
# @Author  : Youwei Wu
# @File    : account.py
# @Software: PyCharm

import os
import time

import pandas as pd

from utils import send_email

def check_account_info():
    try:
        read_account_info(time.strftime('%Y%m%d'), 'talang2')
        read_account_info(time.strftime('%Y%m%d'), 'talang3')
    except Exception as e:
        print(e)
        content = rf"""
        今日踏浪account文件数据获取失败，请检查，五分钟后重试
        文件路径：
        \\192.168.1.116\trade\broker\iQuant\account\Stock\Account-{time.strftime('%Y%m%d')}.csv
        \\192.168.1.116\trade\broker\qmt_gf\account\Stock\Account-{time.strftime('%Y%m%d')}.csv
        \\192.168.1.116\trade\broker\iQuant\account\Stock\Deal-{time.strftime('%Y%m%d')}.csv
        \\192.168.1.116\trade\broker\qmt_gf\account\Stock\Deal-{time.strftime('%Y%m%d')}.csv     
        """
        send_email(
            subject='Alert!!!踏浪账户信息获取失败，请及时更新今日踏浪account文件',
            content=content,
            receiver='wu.yw@yz-fund.com.cn'
        )
        print('踏浪account文件更新失败，5分钟后重试')
        time.sleep(300)
        check_account_info()


def read_account_info(date, account):
    if account == 'talang3':
        key = 'iQuant'
    elif account == 'talang2':
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
    check_account_info()






