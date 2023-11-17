#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/25 8:44
# @Author  : Suying
# @Site    : 
# @File    : live_kline_updater.py

import time
import datetime

import pandas as pd
import rqdatac as rq

from util.send_email import Mail, R
from choice.kc_stock_number import get_kc_stock_num


def gen_quick_virtual_kline(current_minute):
    date = time.strftime('%Y%m%d')
    stock_list = gen_stock_list(date)

    while int(time.strftime('%H%M')) == current_minute:
        print(time.strftime('%X'), 'Wait for update!')
        time.sleep(0.1)
    gen_ricequant_virtual_kline(stock_list, date)


def gen_stock_list(date=None):
    formatted_date = time.strftime('%Y%m%d') if date is None else date
    rq.init()
    cn_stks_df = rq.all_instruments(type='CS', market='cn', date=formatted_date)
    kc_stks_df = cn_stks_df.query("board_type == 'KSH'").set_index('order_book_id')
    return kc_stks_df.index


def gen_ricequant_virtual_kline(stock_list, date=None):
    formatted_date = time.strftime('%Y%m%d') if date is None else date
    current_min = int(time.strftime('%H%M'))
    print(f'Generating RiceQuant virtual kline at {datetime.datetime.now()}')
    rq_vk_df = gen_rq_vk_df(stock_list)
    rq_vk_df.to_pickle(
        rf"\\192.168.1.116\kline\virtual\virtual_kline2_{formatted_date}_{current_min}.pkl")  # for youwei
    rq_vk_df.to_csv(
        rf"\\192.168.1.116\kline\virtual_csv\virtual_kline2_{formatted_date}_{current_min}.csv")  # for shaohu
    print(f'Downloaded at {datetime.datetime.now()}')

    check_rq_virtual_kline(rq_vk_df)
    print(datetime.datetime.now())


def gen_rq_vk_df(stock_list):
    snapshot = rq.current_snapshot(stock_list)
    vk_data = [[x.order_book_id, x.open, x.high, x.low, x.last,
                x.volume, x.total_turnover, x.datetime, x.prev_close] for x in snapshot]
    vk_df = pd.DataFrame(vk_data, columns=[
        'symbol', 'open', 'high', 'low', 'now',
        'volume', 'amount', 'time', 'preclose',
    ])
    vk_df = vk_df.set_index('symbol')
    vk_df['time'] = [float(x.strftime('%H%M%S')) for x in vk_df['time']]
    vk_df.index = ['sh' + x[:6] for x in vk_df.index]
    vk_df.index.name = 'symbol'
    return vk_df


def check_rq_virtual_kline(rq_vk_df):
    kc_stock_num = get_kc_stock_num()
    print('Check RiceQuant virtual kline...')
    error_dict = {
        'NaN stock': rq_vk_df[rq_vk_df.isnull().any(axis=1)].index.tolist(),
        'duplicate stock': rq_vk_df[rq_vk_df.index.duplicated()].index.tolist(),
        'zero': rq_vk_df[(rq_vk_df == 0).any(axis=1)].index.tolist(),
        'negative': rq_vk_df[(rq_vk_df < 0).any(axis=1)].index.tolist(),
        'Open & now out of High & low': rq_vk_df[
            (rq_vk_df['open'] > rq_vk_df['high']) | (rq_vk_df['open'] < rq_vk_df['low']) | (
                    rq_vk_df['now'] > rq_vk_df['high']) | (rq_vk_df['now'] < rq_vk_df['low'])].index.tolist(),

    }
    info_dict = {
        'stock count': rq_vk_df.shape[0],
        'stock count from choice': kc_stock_num,
        'Extreme high low difference': rq_vk_df[
            (rq_vk_df['high'] - rq_vk_df['low']) / rq_vk_df['low'] > 0.50].index.tolist(),
        'Extreme intraday return': rq_vk_df[
            (abs(rq_vk_df['high'] - rq_vk_df['preclose']) / rq_vk_df['preclose']) > 0.21].index.tolist(),
    }
    if all(item == [] for item in list(error_dict.values())) & (
            info_dict['stock count'] == info_dict['stock count from choice']):
        print('No error found in RiceQuant virtual kline')
    else:
        print('Error found in RiceQuant virtual kline, sending email...')
        notify_with_email({**error_dict, **info_dict})


def notify_with_email(error_dict):
    subject = '[Ricequant Virtual Kline] Data Report'
    text = f"""
    <table width="800" border="0" cellspacing="0" cellpadding="4">
    <tr>
    <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>Ricequant Virtual Kline updated</b></td>
    </tr>
    <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
    <p>Virtual Kline has been generated.</p>
    <p>Total number of stock included: {error_dict['stock count']}</p>
    <p>Total number of stock included in last trading day: {error_dict['last day stock count']}</p>
    <p>NaN stock: {error_dict['NaN stock']}</p>
    <p>Duplicate stock: {error_dict['duplicate stock']}</p>
    <p>Zero value stock: {error_dict['zero']}</p>
    <p>Negative value stock: {error_dict['negative']}</p>
    <p>Extreme high low difference: {error_dict['Extreme high low difference']}</p>
    <p>Extreme intraday return: {error_dict['Extreme intraday return']}</p>
    <p>Open & now out of High & low: {error_dict['Open & now out of High & low']}</p>
    
    """
    Mail().send(subject=subject, body_content=text, receivers=R.department['research'][0])
