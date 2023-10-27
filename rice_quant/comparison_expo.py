#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/27 10:32
# @Author  : Suying
# @Site    : 
# @File    : comparison_expo.py
import time

import pandas as pd
from file_location import FileLocation as FL
import rqdatac as rq
import matplotlib.pyplot as plt


def compare_expo(date=None):
    formatted_date = pd.to_datetime(date).strftime('%Y%m%d') if date is not None else time.strftime('%Y%m%d')
    talang_expo_df = gen_expo_history(start='20230908', end=formatted_date)
    factors = talang_expo_df.columns.get_level_values(0).unique()
    for factor in factors:
        single_factor_expo_df = talang_expo_df.loc[:, (factor, slice(None))].droplevel([0,2], axis=1)
        single_factor_expo_df.columns = ['中证1000', '中证500','踏浪2号','踏浪3号']
        plot_single_expo(single_factor_expo_df, factor)


def plot_single_expo(single_factor_expo_df, factor):
    fig = plt.figure(figsize=(10, 6))
    plt.plot(single_factor_expo_df)
    plt.legend(single_factor_expo_df.columns, loc='upper right')
    plt.title(factor, fontsize=20)
    plt.xlabel('Date', fontsize=10)
    plt.ylabel('Exposure', fontsize=10)
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.savefig(fr'.\Data\{factor}对比.png')
    plt.show()
    plt.close()

def gen_expo_history(start, end):
    rq.init()
    date_list = rq.get_trading_dates(start_date=start, end_date=end)
    data = []
    for date in date_list:
        talang_expo_s = get_daily_expo(date)
        print(f'{date} finished processing\n')
        data.append(talang_expo_s)
    talang_expo_df = pd.concat(data, axis=1).T
    return talang_expo_df


def get_daily_expo(date):
    formatted_date = pd.to_datetime(date).strftime('%Y%m%d')
    exposure_save_dir = FL().exposure_dir
    expo_df = pd.read_csv(fr'{exposure_save_dir}\expo_{formatted_date}.csv', index_col=0, header=[0, 1], encoding='gbk')
    talang_expo_df = expo_df.loc[:, (['talang2', 'talang3'], slice(None))]
    talang_expo_df = talang_expo_df.loc[:, (slice(None), ['port', '000905.XSHG','000852.XSHG'])]
    talang_expo_df = talang_expo_df.loc[['liquidity', 'book_to_price', 'leverage', 'residual_volatility'],:]

    talang_expo_s = talang_expo_df.stack().stack().rename(date)
    return talang_expo_s




if __name__ == '__main__':
    compare_expo(date='20231026')