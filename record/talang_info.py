# -*- coding: utf-8 -*-
# @Time    : 2023/7/4 15:27
# @Author  : Youwei Wu
# @File    : talang_info.py
# @Software: PyCharm

import os
import time

import pandas as pd
from file_location import FileLocation as FL
from util.utils import send_email


def read_account_info(date, account):
    account_dir = FL().account_info_dir_dict[account]
    account_code = FL().stock_account_code_dict[account]
    try:
        if account == 'talang2' or account == 'talang3':
            info = pd.read_csv(f'{account_dir}/Account-{date}.csv', encoding='gbk').set_index('资金账号').loc[account_code]
            trades = pd.read_csv(f'{account_dir}/Deal-{date}.csv', encoding='gbk')
            account_info_s = pd.Series({
                '账户': account,
                '交易日': date,
                '总资产': info['总资产'],
                '股票总市值': info['股票总市值'],
                '成交额': trades['成交金额'].sum()
            })
        elif account == 'talang1':
            formatted_date = pd.to_datetime(date).strftime("%Y-%m-%d")
            info = pd.read_csv(rf'{account_dir}/StockFund_{formatted_date}.csv', index_col=False).set_index('账户').loc[
                account_code]
            trades = pd.read_csv(rf'{account_dir}/TransactionsStatisticsDaily_{formatted_date}.csv',
                            index_col=False).set_index(
                    '账户').loc[account_code]
            account_info_s = pd.Series({
                '账户': account,
                '交易日': date,
                '总资产': info['账户资产'],
                '股票总市值': info['证券市值'],
                '成交额': trades['成交额'].sum()
            })
        else:
            raise ValueError('account must be talang1, talang2 or talang3')
        print(account_info_s)
        return account_info_s

    except Exception as e:
        print(e)
        content = rf"""\
        <table width="800" border="0" cellspacing="0" cellpadding="4">
        <tr>
        <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>踏浪23今日盘后账户数据获取</b></td>
        </tr>
        <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
        <p>今日踏浪account文件数据获取失败，请检查，五分钟后重试</p>
        <p>文件路径：</p>
        {account_dir}\Account-{date}.csv
        {account_dir}\Deal-{date}.csv
        """
        send_email(
            subject='Alert!!!踏浪账户信息获取失败，请及时更新今日踏浪account文件',
            content=content,
            receiver='wu.yw@yz-fund.com.cn'
        )
        print('踏浪account文件更新失败，5分钟后重试')
        time.sleep(300)
        read_account_info(date=date, account=account)


if __name__ == '__main__':
    read_account_info(date='20230928', account='talang1')











