#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/3/28 10:30
# @Author  : Suying
# @Site    : 
# @File    : concat_all_data.py
import time
import pandas as pd
import rqdatac as rq

from prepare_arbitrage_daily_data.filter_security_lst import get_filtered_convertible_pair
from prepare_arbitrage_daily_data.get_conversion_price import get_conversion_price
from prepare_arbitrage_daily_data.get_stock_sell_limit import get_stock_sell_price_limit
from util.send_email import Mail, R
from regular_update.position_check import AccountPosition


def concat_all_data(date=None, premium_thresh=0.05):
    rq.init()
    formatted_date = date if date is not None else time.strftime('%Y%m%d')
    pair_df = get_filtered_convertible_pair(premium_thresh=premium_thresh, date=formatted_date)
    conversion_price = get_conversion_price(pair_df.index.tolist(), date=formatted_date)
    stock_sell_price_limit = get_stock_sell_price_limit(pair_df['stock_code'].tolist(), date=formatted_date)
    stock_sell_price_limit['conv_ticker'] = pair_df.index

    panlan1_pos = AccountPosition('盼澜1号', date).get_actual_position()['实际'].rename('stock_volume')
    panlan1_pos.index.names = ['stock_code']

    daily_data = pd.concat([pair_df, conversion_price], axis=1)

    daily_data = daily_data.merge(stock_sell_price_limit, left_on='stock_code', right_index=True)

    stock_code_lst = daily_data['stock_code'].tolist()
    daily_data['stock_code'] = daily_data['stock_code'].str.split('.').str[0]
    daily_data = daily_data.merge(panlan1_pos, left_on='stock_code', right_index=True, how='left')
    daily_data['stock_volume'] = daily_data['stock_volume'].fillna(0)
    daily_data['stock_code'] = stock_code_lst

    daily_data = daily_data[['symbol',
                             'stock_code',
                             'last_premium',
                             'conversion_price',
                             'stock_sell_limit',
                             'credit_volume',
                             'stock_volume'
                             ]]

    save_path = rf'\\192.168.1.116\trade\reference\arbitrage\target_pair_{formatted_date}.csv'
    daily_data.to_csv(save_path)
    print(rf'All data has been saved to {save_path}')

    daily_data = daily_data.reset_index()
    daily_data.index = daily_data.index + 1

    df_html = daily_data.to_html()

    content = f"""
    <table width="800" border="0" cellspacing="0" cellpadding="4">
    <tr>
    <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>[折价套利标的数据]已生成</b></td>
    </tr>
    <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
    """
    content += f"""
    <p>[折价套利标的数据{date}]已生成</p>
    <p>文件路径：{save_path}</p>
    <p>根据st、中信融券、转股期、前一交易日转股溢价率不高于{premium_thresh}条件筛选标的数据</p>
    <center>{df_html}</center>
    """

    Mail().send(
        subject=f'[折价套利标的数据{formatted_date}]已生成',
        body_content=content,
        receivers=R.department['research'] + [R.staff['ling']],
        attachs=[save_path]

    )
