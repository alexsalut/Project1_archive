#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/3/8 16:37
# @Author  : Suying
# @Site    : 
# @File    : get_close_price.py

import time
import pandas as pd
import rqdatac as rq


def get_close_price(date=None):
    date = time.strftime('%Y%m%d') if date is None else pd.to_datetime(date).strftime('%Y%m%d')
    year = date[:4]
    month = date[:6]
    stock_path = rf'\\192.168.1.116\tushare\price\daily\raw\{year}\{month}\raw_daily_{date}.csv'
    conv_path = rf'C:\Users\Yz02\Desktop\Data\conv_adjusted_daily_bar\convertible_adjusted_daily_bar\{year}\adjusted_daily_bar_{date}.csv'
    yhrl_etf_path = rf'C:\Users\Yz02\Desktop\Data\银华日利etf.csv'
    conv_etf_path = rf'C:\Users\Yz02\Desktop\Data\可转债etf.csv'

    stock_s = pd.read_csv(stock_path).set_index('ts_code')['close']
    conv_s = pd.read_csv(conv_path).set_index('ticker')['close']
    etf_s = pd.read_csv(yhrl_etf_path).set_index('date')['close']
    etf_s.index = pd.to_datetime(etf_s.index)
    conv_etf = pd.read_csv(conv_etf_path).set_index('日期')['close']
    conv_etf.index = pd.to_datetime(conv_etf.index)
    rq.init()
    if date not in etf_s.index:

        etf_s.loc[date] = rq.get_price('511880.XSHG', start_date=date, end_date=date, fields='close').iloc[0, 0]
        etf_s.to_csv(yhrl_etf_path)
    if date not in conv_etf.index:
        conv_etf.loc[date] = rq.get_price('511380.XSHG', start_date=date, end_date=date, fields='close').iloc[0, 0]
        conv_etf.to_csv(conv_etf_path)
    close = pd.concat([stock_s,
                       conv_s,
                       pd.Series({'511880.XSHG': etf_s.loc[date]}),
                       pd.Series({'511380.XSHG': conv_etf.loc[date]})],axis=0).rename('收盘价')
    close.index = close.index.str.split('.').str[0]
    return close