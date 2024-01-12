#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/12/14 10:52
# @Author  : Suying
# @Site    : 
# @File    : Matic_normal_clearing_ret_analysis.py

import pandas as pd
import time
import rqdatac as rq

from util.trading_calendar import TradingCalendar as tc


def hold_pl(date=None):
    date = time.strftime('%Y%m%d') if date is None else date
    last_trading_day = tc().get_n_trading_day(date, -1).strftime('%Y%m%d')
    path = rf'C:\Users\Yz02\Desktop\Data\Save\账户对账单\666810075512_衍舟弄潮1号_普通账单_HT1_{last_trading_day}.xlsx'
    df = pd.read_excel(path, header=1, index_col=0, sheet_name='持仓清单').dropna()
    df['证券代码'] = df['证券代码'].astype(int).astype(str)
    rq.init()
    ticker_list = rq.all_instruments(type='Convertible').order_book_id.tolist()
    ticker_dict = {ticker[:6]: ticker for ticker in ticker_list}
    df['ticker'] = df['证券代码'].map(ticker_dict)
    df = df.dropna()
    df = df.set_index('ticker', drop=True)
    conv_df = rq.get_price(df.index.tolist(), start_date=date, end_date=date, frequency='1d').droplevel(1)
    conv_df['pct_chg'] = conv_df['close'] / conv_df['prev_close'] - 1
    df['pct_chg'] = conv_df['pct_chg']
    df['盈亏'] = df['参考市值'].mul(df['pct_chg'])
    return df['盈亏'].sum(), df[['参考市值', 'pct_chg', '盈亏']]


def matic_clearing_trade_pl(date=None):
    date = time.strftime('%Y%m%d') if date is None else date
    path = rf'C:\Users\Yz02\Desktop\Data\Save\账户对账单\666810075512_衍舟弄潮1号_普通账单_HT1_{date}.xlsx'
    df = pd.read_excel(path, header=1, index_col=0, sheet_name='对账单')
    df = df.query('业务标志 == "证券买入" or 业务标志 == "证券卖出"')
    df['交易方向'] = df['业务标志'].map({'证券买入': 1, '证券卖出': -1})
    df['成交股数'] = df['成交股数'] * df['交易方向'] * df['数量单位']
    df['成交金额'] = df['成交金额'] * df['交易方向']
    sumup = df.groupby('证券代码').sum()
    sumup.index = sumup.index.astype(int).astype(str)
    rq.init()
    ticker_list = rq.all_instruments(type='Convertible').order_book_id.tolist()
    ticker_dict = {ticker[:6]: ticker for ticker in ticker_list}
    sumup['ticker'] = sumup.index.map(ticker_dict)
    sumup = sumup.set_index('ticker', drop=True)
    tickers = sumup.index[:-1].tolist()
    pct = rq.get_price(tickers, start_date=date, end_date=date, frequency='1d', fields='close').droplevel(1)
    sumup['close'] = pct
    sumup['收盘金额'] = sumup['成交股数'] * sumup['close']
    sumup['盈亏'] = sumup['收盘金额'] - sumup['成交金额']
    profit = sumup['盈亏'].sum()
    return profit, sumup[['成交股数', '成交金额', '收盘金额', '盈亏']]
