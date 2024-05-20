#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/3/28 8:56
# @Author  : Suying
# @Site    : 
# @File    : filter_security_lst.py
import os
import time
import pandas as pd
import glob

import rqdatac as rq
from util.send_email import Mail, R

rq.init()


def get_filtered_convertible_pair(premium_thresh=0.05, date=None):
    formatted_date = date if date is not None else time.strftime('%Y%m%d')
    last_trading_day = rq.get_previous_trading_date(formatted_date, 1).strftime('%Y%m%d')

    pair = rq.convertible.all_instruments(formatted_date).set_index('order_book_id')[['stock_code', 'symbol']]
    rq_stock_dict, rq_stock_lst = get_citic_rq(date)

    daily_rong_quan_path = rf'\\192.168.1.116\trade\reference\data\quan_available_{formatted_date}.csv'
    if not os.path.exists(daily_rong_quan_path):
        print(f'{daily_rong_quan_path} does not exist, please check the path, retry in 2 mins')
        Mail().send(
            subject=f'{formatted_date}今日已融券文件不存在，请检查生成',
            body_content=f'{daily_rong_quan_path}不存在，请检查数据路径',
            receivers=[R.staff['liu']] + [R.staff['zhou']]
        )
        time.sleep(120)

    rq_volume = pd.read_csv(daily_rong_quan_path, index_col=0).set_index('symbol')['qty'].rename('credit_volume')
    rq_volume.index = rq_volume.index.str.replace('SH', 'XSHG').str.replace('SZ', 'XSHE')
    pair = pair.merge(rq_volume, left_on='stock_code', right_index=True, how='outer')

    indicators = rq.convertible.get_indicators(pair.index.tolist(),
                                               start_date=last_trading_day,
                                               end_date=last_trading_day)['conversion_premium'].droplevel(1)
    pair_s = indicators.rename('last_premium')

    pair_df = pd.concat([pair, pair_s], axis=1)
    instant_rq_lst = [stock for stock in pair_df['stock_code'].tolist() if stock in rq_stock_dict['实时券单']]
    appoint_rq_lst = [stock for stock in pair_df['stock_code'].tolist() if stock in rq_stock_dict['经纪券单(预约)']]

    def get_rongquan_type(x):
        if x['stock_code'] in instant_rq_lst and x['stock_code'] in appoint_rq_lst:
            return 'both'
        elif x['stock_code'] in appoint_rq_lst:
            return 'appoint'
        elif x['stock_code'] in instant_rq_lst:
            return 'instant'
        else:
            return 'None'

    pair_df['rq_type'] = pair_df.apply(lambda x: get_rongquan_type(x), axis=1)
    pair_df['credit_volume'] = pair_df['credit_volume'].fillna(0)
    pair_df = pair_df.sort_values(['credit_volume', 'last_premium'], ascending=[False, True])
    filtered_pair_df = pair_df.query(
        f'(last_premium <= {premium_thresh} and rq_type!="None") or stock_code in {rq_volume.index.tolist()}')
    filtered_pair_df = filtered_pair_df.query('stock_code not in @st_stock_lst')
    filtered_pair_df = filtered_pair_df.query('order_book_id in @conversion_convs')
    return filtered_pair_df


def get_last_5days_st_stock():
    path = r'\\192.168.1.116\kline\st_list.csv'
    if not os.path.exists(path):
        print(f'{path} does not exist, please check the path, retry in 10 seconds')
        time.sleep(10)
        return get_last_5days_st_stock()

    st = pd.read_csv(path, index_col=0)
    stock_lst = st.index.tolist()
    formatted_stock_lst = rq.id_convert(stock_lst)
    return formatted_stock_lst


def get_citic_rq(date=None):
    Mail().receive(date_range=[2, 1], save_dir=r'D:\data\中信券源\raw', file_list=['CITIC_SBL_Securities_List'])
    formatted_date = date if date is not None else time.strftime('%Y%m%d')
    formatted_date2 = pd.to_datetime(formatted_date).strftime('%Y-%m-%d')
    path_lst = glob.glob(rf'D:\data\中信券源\raw\CITIC_SBL_Securities_List*.xlsx')
    filtered_path_lst = [path for path in path_lst if formatted_date in path or formatted_date2 in path]

    time_list = [os.path.getmtime(file) for file in filtered_path_lst]
    path = filtered_path_lst[time_list.index(max(time_list))]
    print(f'path: {path}')

    if not os.path.exists(path):
        print(f'{path} does not exist, please check the path, retry in 10 seconds')
        time.sleep(10)
        return get_citic_rq(date=date)

    sheets = pd.ExcelFile(path).sheet_names
    stock_dict = {}
    stock_lst = []
    for sheet in sheets:
        if sheet != '公募券单(预约)' and sheet != '篮子下单(预约,按权重)':
            data = pd.read_excel(path, sheet_name=sheet, converters={'证券代码': str}, index_col=0, header=0)
            data.index = data.index.astype(str).str.zfill(6)
            rq_lst = rq.id_convert(list(set(data.index.tolist())))
            stock_dict[sheet] = rq_lst
            stock_lst.extend(rq_lst)

    stock_lst = list(set(stock_lst))
    return stock_dict, stock_lst
