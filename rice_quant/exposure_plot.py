#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/24 14:05
# @Author  : Suying
# @Site    : 
# @File    : exposure_plot.py

import os

import pandas as pd
import numpy as np
import rqdatac as rq

from util.file_location import FileLocation as FL
from matplotlib import pyplot as plt


def plot_all_barra_expo(date=None):
    formatted_date = pd.to_datetime(date).strftime('%Y%m%d')
    barra_df = gen_relative_barra_expo_history(start='20230908', end=formatted_date)
    barra_df.index = pd.MultiIndex.from_tuples(
        [(i[0], '踏浪1号' if i[1] == 'panlan' else i[1]) for i in barra_df.index])
    file_list = []
    for factor in barra_df.columns:
        file_path = plot_single_barra_expo(barra_df[factor])
        file_list.append(file_path)
    return file_list


def plot_single_barra_expo(barra_s):
    factor = barra_s.name
    expo_df = barra_s.unstack()
    fig, ax = plt.subplots(3, 1, figsize=(20, 15), sharex=True)
    for i, account in enumerate(expo_df.columns):
        ax[i].bar(np.arange(len(expo_df.index)), expo_df[account].values)
        ax[i].grid()
        ax[i].set_title(account)

    plt.xlabel('Date')
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.locator_params(axis='x', nbins=10)
    plt.rcParams['axes.unicode_minus'] = False
    plt.xticks(np.arange(len(expo_df.index))[::5], expo_df.index[::5], rotation=45)

    plt.suptitle(factor, fontsize=20)
    os.makedirs(fr'{FL().exposure_dir}\Data', exist_ok=True)
    path = fr'{FL().exposure_dir}\Data\{factor}.png'
    plt.savefig(path)
    return path


def gen_relative_barra_expo_history(start, end):
    rq.init()
    date_list = rq.get_trading_dates(start_date=start, end_date=end)
    data = []
    for date in date_list:
        df = gen_relative_barra_expo(date)
        print(f'{date} finished processing')
        data.append(df)
    barra_df = pd.concat(data, axis=1).T
    return barra_df


def gen_relative_barra_expo(date):
    formatted_date = pd.to_datetime(date).strftime('%Y%m%d')
    exposure_save_dir = FL().exposure_dir
    expo_df = pd.read_csv(fr'{exposure_save_dir}\expo_{formatted_date}.csv', index_col=0, header=[0, 1], encoding='gbk')
    relative_df = expo_df.loc[:, (slice(None), 'relative')].droplevel(1, axis=1)
    barra_relative_df = relative_df.loc[:'residual_volatility']
    barra_relative_df = barra_relative_df.rename(columns={
        'panlan': '踏浪1号',
        'talang1': '踏浪1号',
        'talang2': '踏浪2号',
        'talang3': '踏浪3号',
    })
    barra_relative_df.columns = pd.MultiIndex.from_product([[date], barra_relative_df.columns])
    return barra_relative_df
