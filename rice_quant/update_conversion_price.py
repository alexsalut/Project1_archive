#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/4/8 16:49
# @Author  : Suying
# @Site    : 
# @File    : update_conversion_price.py

import time
import pandas as pd
import rqdatac as rq

def download_conversion_price(year='2024', date=None):
    start = year + '0101'
    end = time.strftime('%Y%m%d') if date is None else date
    rq.init()
    trading_dates = [pd.to_datetime(date) for date in rq.get_trading_dates(start, end)]

    conv_info = rq.convertible.all_instruments().set_index('order_book_id')
    trading_conv_info = conv_info.query('(stop_trading_date > @start)|(stop_trading_date.isnull())')
    conv_list = trading_conv_info.index.tolist()

    conv_p_df = rq.convertible.get_conversion_price(conv_list)
    data = []
    for conv in conv_p_df.index.get_level_values(0).unique():
        single_conv_df = conv_p_df.loc[conv].set_index('effective_date')
        selected_dates = trading_dates
        selected_dates += single_conv_df.index.tolist()
        selected_dates = list(set(selected_dates))
        expand_conv_df = single_conv_df.reindex(selected_dates).sort_index(ascending=True)[['conversion_price']]
        expand_conv_df = expand_conv_df.ffill()
        expand_conv_df = expand_conv_df.dropna(how='all')
        expand_conv_df = expand_conv_df[expand_conv_df.index >= pd.to_datetime(start)]
        expand_conv_df['order_book_id'] = conv
        expand_conv_df = expand_conv_df.set_index('order_book_id', append=True).swaplevel()
        data.append(expand_conv_df)
        print(f'{conv} done')
    conv_p_df = pd.concat(data, axis=0)
    conv_p_df = conv_p_df.rename(columns={'effective_date': 'date'})
    conv_p_df = conv_p_df.swaplevel(0, 1)
    path = rf'D:\data\conversion_price\conversion_price_{year}.pkl'
    conv_p_df.to_pickle(path)