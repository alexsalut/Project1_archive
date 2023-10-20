#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/23 17:54
# @Author  : Suying
# @Site    : 
# @File    : account_info.py
import time
import pandas as pd
from rolling_check.panlan1_info import Panlan1AccountInfo
from rolling_check.tinglian2_info import get_tinglian2_raw_info
from util.trading_calendar import TradingCalendar as TC


def output_account_pl(account, date=None, stock_inflow=0, option_inflow=0):
    account_pl_dict = get_account_pl(account, date, stock_inflow, option_inflow)
    account_name = '盼澜1号' if account == 'panlan1' else '听涟2号'
    account_pl_output = [f"{account_pl_dict['time']}\n",
                         f"{account_name}，",
                         f"股票盈亏：{account_pl_dict['stock pl']:.2f}，",
                         f"期权盈亏：{account_pl_dict['option pl']:.2f}，",
                         f"涨跌幅：{account_pl_dict['daily return']:.3%}，",
                         f"昨日权益：{account_pl_dict['last total equity']:.2f}，",
                         f"今日权益：{account_pl_dict['total equity']:.2f}，",]
    if account == 'panlan1':
        account_pl_output.append(f"保证金风险度：{account_pl_dict['margin risk']}，")
    print(''.join(account_pl_output))
    time.sleep(3)
    return ''.join(account_pl_output)

def get_account_pl(account, date=None, stock_inflow=0, option_inflow=0):
    formatted_date = time.strftime('%Y%m%d') if date is None else pd.to_datetime(date).strftime("%Y%m%d")
    last_trading_day = TC().get_n_trading_day(date=formatted_date,n=-1).strftime('%Y%m%d')
    last_trading_day_account_info = get_account_info(account, last_trading_day)
    today_account_info = get_account_info(account, formatted_date)
    today_account_info['time'] = time.strftime('%Y-%m-%d %X')
    today_account_info['stock pl'] = today_account_info['stock equity'] - last_trading_day_account_info['stock equity'] - stock_inflow
    today_account_info['option pl'] = today_account_info['option equity'] - last_trading_day_account_info['option equity'] - option_inflow
    today_account_info['total pl'] = today_account_info['stock pl'] + today_account_info['option pl']
    today_account_info['total equity'] = today_account_info['stock equity'] + today_account_info['option equity']
    today_account_info['last total equity'] = last_trading_day_account_info['stock equity'] + last_trading_day_account_info['option equity']
    today_account_info['daily return'] = today_account_info['total pl'] / (last_trading_day_account_info['stock equity'] + last_trading_day_account_info['option equity'])
    return today_account_info

def get_account_info(account, date=None):
    date = time.strftime('%Y%m%d') if date is None else pd.to_datetime(date).strftime("%Y%m%d")
    if account == 'panlan1':
        return Panlan1AccountInfo().get_panlan1_account_info(date)
    elif account == 'tinglian2':
        return get_tinglian2_raw_info(date)
    else:
        print('Error: 请检查账户名称是否正确，目前只支持盼澜1号和听涟2号')
        return None


