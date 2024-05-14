#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/3/1 8:52
# @Author  : Suying
# @Site    : 
# @File    : product_ret_comparison.py


import pandas as pd
import numpy as np
import rqdatac as rq

import matplotlib.pyplot as plt


def get_product_excess_ret_comparison(start='20231108', end='20240229', product_list=['踏浪1号', '盼澜1号']):
    df = get_product_excess_ret(start=start, end=end, product_list=product_list)
    df['踏浪1号相对日胜'] = (df['踏浪1号'] > df['盼澜1号']).astype(int).cumsum() / np.arange(1, len(df) + 1)
    df['踏浪1号超额净值'] = (df['踏浪1号'] + 1).cumprod()
    df['盼澜1号超额净值'] = (df['盼澜1号'] + 1).cumprod()
    df.loc['2023-11-07', ['踏浪1号超额净值', '盼澜1号超额净值']] = [1, 1]
    df = df.sort_index(ascending=True)

    plt.figure(figsize=(20, 15))
    plt.plot(df['踏浪1号超额净值'], marker='o', label='踏浪1号')
    plt.plot(df['盼澜1号超额净值'], marker='o', label='盼澜1号')

    plt.legend()
    plt.grid()
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.title('踏浪1号和盼澜1号超额净值表现')
    plt.xticks(rotation=45)
    plt.xlabel('日期')
    plt.ylabel('超额净值')
    plt.tight_layout()
    plt.savefig(rf'踏浪1号和盼澜1号超额净值表现.png')
    plt.close()

    plt.figure(figsize=(20, 15))
    plt.plot(df['踏浪1号相对日胜'], marker='o', label='踏浪1号相对日胜率')
    plt.legend()
    plt.grid()
    plt.xticks(rotation=45)
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.title('踏浪1号相对日胜率')
    plt.xlabel('日期')
    plt.ylabel('相对日胜率')
    plt.tight_layout()
    plt.savefig(rf'踏浪1号相对日胜率.png')
    plt.close()


def get_product_excess_ret(start, end, product_list):
    rq.init()
    dates = rq.get_trading_dates(start, end)
    dates = [date.strftime('%Y%m%d') for date in dates]
    data = []
    for date in dates:
        s = get_daily_product_excess_ret(date=date, product_list=product_list)
        data.append(s)
    df = pd.DataFrame(data)
    return df


def get_daily_product_excess_ret(date, product_list):
    path = rf'\\192.168.1.116\target_position\monitor\monitor_{date}.xlsx'
    monitor_df = pd.read_excel(path, sheet_name=0, header=None, index_col=False)

    excess_ret_dict = {}
    for product in product_list:
        excess_ret_dict[product] = get_valus(monitor_df, product)
    return pd.Series(excess_ret_dict).rename(date)


def get_valus(df, indicator):
    loc = np.where(df.apply(lambda x: x.astype(str).str.contains(indicator)))
    product = df.iloc[loc[0][0], loc[1][0]]
    ret_s = df.iloc[loc[0][0], :].dropna()
    new_loc = np.where(ret_s.values == product)
    return ret_s.iloc[new_loc[0][0] + 2]


if __name__ == '__main__':
    get_product_excess_ret_comparison()
