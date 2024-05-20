#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/3/28 10:20
# @Author  : Suying
# @Site    : 
# @File    : get_stock_sell_limit.py
import time
import rqdatac as rq


def get_stock_sell_price_limit(stock_list, date=None):
    """
    获取下一个交易日的跌停价
    :param stock_list:
    :param date:
    :return:
    """
    rq.init()
    formatted_date = date if date is not None else time.strftime('%Y%m%d')
    last_trading_day = rq.get_previous_trading_date(formatted_date, 1).strftime('%Y%m%d')
    stock_df = rq.get_price(stock_list, start_date=last_trading_day, end_date=last_trading_day, fields='close')
    stock_df['stock_sell_limit'] = stock_df.apply(
        lambda x: x['close'] * 0.805
        if x.name[:2] == '30' or x.name[:2] == '68'
        else x['close'] * 0.905, axis=1)
    stock_df = stock_df.rename(columns={'close': 'prev_close'})
    stock_df = stock_df.droplevel(1)
    return stock_df
