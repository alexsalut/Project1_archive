#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/3/28 10:11
# @Author  : Suying
# @Site    : 
# @File    : get_conversion_price.py
import time
import rqdatac as rq


def get_conversion_price(conv_list, date=None):
    formatted_date = date if date is not None else time.strftime('%Y%m%d')
    conv_p_df = rq.convertible.get_conversion_price(conv_list)
    filter_conv_p_df = conv_p_df[conv_p_df['effective_date'] <= formatted_date]
    filter_conv_p_df = filter_conv_p_df.sort_index(ascending=True).groupby(level=0).last()
    conversion_price = filter_conv_p_df['conversion_price']
    return conversion_price
