#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/3/22 15:39
# @Author  : Suying
# @Site    : 
# @File    : get_citic_rq.py

import glob
import time
import os
import pandas as pd

import rqdatac as rq
from regular_update.rzrq_limit import download_citic_rq_file


def get_citic_rq(date=None, year='2024'):
    rq.init()
    formatted_date1 = date if date is not None else time.strftime('%Y%m%d')
    download_citic_rq_file(formatted_date1)
    dir = r'D:\data\中信券源\raw'
    files = glob.glob(dir + '/*.xlsx')
    trading_dates = rq.get_trading_dates(f'{year}0101', formatted_date1)
    dates1 = [date.strftime('%Y%m%d') for date in trading_dates]

    rq_s = pd.Series(index=dates1)
    for date in dates1:
        date_v1 = pd.to_datetime(date).strftime('%Y-%m-%d')
        filtered_files = [file for file in files if date in file or date_v1 in file]
        if len(filtered_files) == 0:
            print(f'{date} has no file')
        else:
            file = filtered_files[0]
            rq_s[date] = get_rzrq_list(file)
    rq_s = rq_s.sort_index()
    rq_s.to_pickle(rf'D:\data\中信券源\citic_rq_list{year}.pkl')


def get_rzrq_list(file):
    sheets = pd.ExcelFile(file).sheet_names
    stock_lst = []
    for sheet in sheets:
        if sheet != '公募券单(预约)' and sheet != '篮子下单(预约,按权重)':
            data = pd.read_excel(file, sheet_name=sheet, converters={'证券代码': str}, index_col=0, header=0)
            data.index = data.index.astype(str).str.zfill(6)
            stock_lst += data.index.tolist()
    rq_list = list(set(stock_lst))
    return rq_list


if __name__ == '__main__':
    get_citic_rq(date='20211231', year='2021')