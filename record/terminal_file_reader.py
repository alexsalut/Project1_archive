#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/5/7 9:47
# @Author  : Suying
# @Site    : 
# @File    : terminal_file_reader.py

import os
import time
import pandas as pd
import numpy as np
import rqdatac as rq
from record.cats_terminal_reader import CatsFileReader
from record.matic_terminal_reader import MaticFileReader
from util.send_email import Mail, R
from record.get_clearing_info import SettleInfo
def read_terminal_file(dir, account, account_code=None, date=None):
    if account == '中信普通账户':
        return read_cats_normal_account(dir, account_code, date)
    elif account == '中信信用账户':
        return read_cats_credit_account(dir, account_code, date)
    elif account == '华泰普通账户':
        return read_matic_normal_account(dir, account_code, date)
    elif account == '华泰信用账户':
        return read_matic_credit_account(dir, account_code, date)
    elif account == '中信期权账户':
        return read_cats_option_acccount(dir, account_code, date)
    elif account == '东财信用账户':
        return read_emc_credit_account(dir, account_code, date)
    elif account == '华安普通账户':
        return read_ha_normal_account(dir, account_code, date)
    elif account == '华泰期货账户':
        return read_matic_future_account(dir, account_code, date)
    elif account == '东证期货账户':
        return read_dz_future_account(dir, date)
    elif account == '财达普通账户':
        return read_cd_normal_account(dir, account_code, date)


def read_cd_normal_account(dir, account_code, date):
    date = pd.to_datetime(date).strftime('%Y%m%d') if date is not None else time.strftime('%Y%m%d')
    fund_df = pd.read_csv(f'{dir}/Account-{date}.csv', encoding='gbk')
    fund_s = fund_df.set_index('资金账号').loc[account_code]
    trade_df = pd.read_csv(f'{dir}/Deal-{date}.csv', encoding='gbk').set_index('资金账号')
    if account_code in trade_df.index:
        transaction = trade_df.loc[account_code, '成交金额'].sum()
    else:
        transaction = 0
    account_info_dict = {
        '账户净资产': float(fund_s['总资产']),
        '证券市值': fund_s['总市值'],
        '成交额': transaction
    }
    return account_info_dict

def read_dz_future_account(dir, date):
    rq.init()
    date = pd.to_datetime(date).strftime('%Y%m%d') if date is not None else time.strftime('%Y%m%d')
    last_trading_day = rq.get_previous_trading_date(date, 1).strftime('%Y%m%d')

    last_equity = SettleInfo(date=last_trading_day).get_settle_info(account='听涟1号')['期货权益']

    pos_path = f'{dir}/听涟1号_pos_{date}.csv'
    last_pos_path = f'{dir}/听涟1号_pos_{last_trading_day}.csv'
    trade_path = f'{dir}/听涟1号_trade_{date}.csv'
    if not os.path.exists(pos_path) or not os.path.exists(trade_path):
        Mail().send(subject='!!!听涟1号东证期货导出单未生成', body_content=f'东证期货结算单未生成, 请检查', receivers=R.staff['zhou'])
        time.sleep(120)

    trade_df = pd.read_csv(trade_path, encoding='gbk')
    if len(trade_df) == 0:
        transaction = 0
    else:
        trade_df['买卖手数'] = trade_df.apply(lambda x: x['手数'] if '开' in x['开平'] else -x['手数'], axis=1)
        trade_df['成交额'] = trade_df['买卖手数'] * trade_df['成交价格'] * 200 + trade_df['手续费']
        transaction = trade_df.groupby('成交合约')['成交额'].sum().sum()
    pos_df = pd.read_csv(pos_path, encoding='gbk').set_index('持仓合约')
    last_pos = pd.read_csv(last_pos_path, encoding='gbk').set_index('持仓合约')

    hold_cost = last_pos['持仓市值'].sum() + transaction
    pos_cap = pos_df['持仓市值'].sum()
    pl = hold_cost - pos_cap
    account_dict = {
        '账户净资产': pl + last_equity,
        '证券市值': pos_cap,
    }
    return account_dict





def read_ha_normal_account(dir, account_code, date):
    date = pd.to_datetime(date).strftime('%Y%m%d') if date is not None else time.strftime('%Y%m%d')
    info = pd.read_csv(f'{dir}/Account-{date}.csv', encoding='gbk').set_index('资金账号').loc[account_code]
    trades = pd.read_csv(f'{dir}/Deal-{date}.csv', encoding='gbk').set_index('资金账号')
    if account_code in trades.index:
        transaction = trades.loc[account_code, '成交金额'].sum()
        account_trades = trades.loc[account_code]
    else:
        transaction = 0
        account_trades = pd.DataFrame(columns=trades.columns)

    account_info_dict = {
        '股票权益': float(info['总资产']),
        '股票市值': info['总市值'],
        '成交额': transaction,
        '交易记录': account_trades
    }
    return account_info_dict


def read_matic_future_account(dir, account_code, date):
    m = MaticFileReader(dir, account_code, date)
    account_info = m.get_future_account_info()
    return account_info


def read_matic_credit_account(dir, account_code, date):
    m = MaticFileReader(dir, account_code, date)
    account_info = m.get_credit_account_info()
    return account_info

def read_cats_normal_account(dir, account_code, date):
    c = CatsFileReader(dir, account_code, date)
    account_info = c.get_normal_account_info()
    return account_info

def read_cats_credit_account(dir, account_code, date):
    c = CatsFileReader(dir, account_code, date)
    account_info = c.get_credit_account_info()
    return account_info

def read_matic_normal_account(dir, account_code, date):
    m = MaticFileReader(dir, account_code, date)
    account_info = m.get_normal_account_info()
    return account_info


def read_cats_option_acccount(dir, account_code, date):
    c = CatsFileReader(dir, account_code, date)
    account_info = c.get_option_account_info()
    return account_info


def read_emc_credit_account(dir, account_code, date):
    date = pd.to_datetime(date).strftime("%Y%m%d") if date is not None else time.strftime('%Y%m%d')
    stock_df = pd.read_csv(
        rf'{dir}/310310300343_RZRQ_FUND.{date}.csv',
        index_col=False,
        encoding='gbk'
    )
    stock_equity = stock_df.loc[0, '资产总值'] - stock_df.loc[0, '总负债']


    trade_path = rf'{dir}/310310300343_RZRQ_MATCH.{date}.csv'
    if not os.path.exists(trade_path):
        stock_transaction_vol = 0
    else:
        transaction_df = pd.read_csv(
            trade_path,
            index_col=False,
            encoding='gbk'
        )

        stock_transaction_df = transaction_df.query(f'资金账号=={account_code}|业务类型.isin(["证券买入", "证券卖出"])')
        stock_transaction_vol = stock_transaction_df['成交数量'].mul(stock_transaction_df['成交价格']).sum()

    account_info = {
        '账户净资产': stock_equity,
        '证券市值': stock_df.loc[0, '总市值'],
        '成交额': stock_transaction_vol,
    }
    return account_info

def get_value(df, string, i, j):
    loc = np.where(df.values == string)
    return df.iloc[loc[0][0] + i, loc[1][0] + j]

