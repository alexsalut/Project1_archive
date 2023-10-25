#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/24 14:05
# @Author  : Suying
# @Site    : 
# @File    : exposure_plot.py
import pandas as pd

from file_location import FileLocation as FL
from matplotlib import pyplot as plt
import numpy as np
import seaborn as sns
import rqdatac as rq
import plotly.subplots as sp
import plotly.graph_objects as go

def plot_all_barra_expo(barra_df):
    for factor in barra_df.columns:
        plot_single_barra_expo(barra_df[factor])


def plot_single_barra_expo(barra_s):
    factor = barra_s.name
    expo_df = barra_s.unstack()
    fig, ax = plt.subplots(3, 1, figsize=(20, 15), sharex=True)
    for i, account in enumerate(expo_df.columns):
        ax[i].bar(np.arange(len(expo_df.index)), expo_df[account].values)
        ax[i].set_title(account)
    plt.xlabel('Date')
    plt.xticks(np.arange(len(expo_df.index)), expo_df.index, rotation=45, ha='right')

    plt.suptitle(factor, fontsize=20)

    plt.savefig(fr'.\Data\{factor}.png')
    # fig = sp.make_subplots(rows=3, cols=1, subplot_titles=expo_df.columns, shared_xaxes=False)
    # for i, account in enumerate(expo_df.columns):
    #     fig.add_trace(go.Bar(x=expo_df.index, y=expo_df[account].values, name=account), row=i+1, col=1)
    # fig.update_layout(title_text=factor)
    # fig.show()






def gen_relative_barra_expo_history(start, end):
    rq.init()
    date_list = rq.get_trading_dates(start_date=start, end_date=end)
    data = []
    for date in date_list:
        df = gen_relative_barra_expo(date)
        print(f'{date} finished processing\n')
        data.append(df)
    barra_df = pd.concat(data, axis=1).T
    return barra_df


def gen_relative_barra_expo(date):
    formatted_date = pd.to_datetime(date).strftime('%Y%m%d')
    exposure_save_dir = FL().exposure_dir
    expo_df = pd.read_csv(fr'{exposure_save_dir}\expo_{formatted_date}.csv', index_col=0, header=[0, 1], encoding='gbk')
    relative_df = expo_df.loc[:, (slice(None), 'relative')].droplevel(1, axis=1)
    barra_relative_df = relative_df.loc[:'residual_volatility']
    barra_relative_df.columns = pd.MultiIndex.from_product([[date], barra_relative_df.columns])
    return barra_relative_df


if __name__ == '__main__':
    expo_df = gen_relative_barra_expo_history(start='20230908', end='20231024')
    factor = 'momentum'
    plot_all_barra_expo(expo_df)
