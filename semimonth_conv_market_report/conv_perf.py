#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/3/8 14:05
# @Author  : Suying
# @Site    : 
# @File    : conv_perf.py
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from matplotlib import ticker
from EmQuantAPI import c


def gen_all_graph(start, end, save_dir):
    c.start("ForceLogin=1")
    debt_nav, debt_ret = get_index_perf(start, end, '债')
    stock_nav, stock_ret = get_index_perf(start, end, '股')
    yearly_debt_nav, yearly_debt_ret = get_index_perf('20240101', end, '债')
    yearly_stock_nav, yearly_stock_ret = get_index_perf('20240101', end, '股')
    yearly_index_nav = pd.concat([yearly_debt_nav, yearly_stock_nav], axis=1)
    yearly_ind_nav, yearly_ind_ret = get_index_perf('20240101', end, '行业')
    ind_nav, ind_ret = get_index_perf(start, end, '行业')
    c.stop()

    plot_index_nav(yearly_ind_nav, save_dir, title=f'2024年东财可转债行业指数走势', vertical=start, date=True)

    plot_index_nav(
        yearly_index_nav,
        save_dir,
        title=f'2024年可转债和股票指数走势',
        vertical=start,
        date=True,
        dotted_index_lst=['国债', '上证转债', '深证转债', '国证转债']
    )
    plot_index_nav(pd.concat([debt_nav, stock_nav], axis=1),
                   save_dir,
                   title=f'近两周可转债和股票指数({start}-{end})走势',
                   dotted_index_lst=['国债', '上证转债', '深证转债', '国证转债'])
    plot_index_ret(pd.concat([debt_ret, stock_ret], axis=0), save_dir,
                   title=f'近两周可转债和股票指数({start}-{end})区间收益', label_size=12)
    plot_index_ret(ind_ret, save_dir, title=f'近两周东财可转债行业指数({start}-{end})区间收益', label_size=7)


def plot_index_nav(index_nav, save_dir, title='近两周主流指数区间净值', date=True, vertical=None,
                   dotted_index_lst=None):
    end_nav = index_nav.iloc[-1]
    sorted_list = end_nav.sort_values(ascending=False).index.tolist()
    index_nav = index_nav[sorted_list]
    if date:
        index_nav.index = index_nav.index.strftime('%Y%m%d')
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111)
    if dotted_index_lst is None:
        index_nav.plot(ax=ax, marker='o')
    else:
        for col in index_nav.columns:
            if col in dotted_index_lst:
                index_nav[col].plot(ax=ax, marker='o')
            else:
                index_nav[col].plot(ax=ax, linestyle='--')

    plt.title(title)
    plt.legend(bbox_to_anchor=(1, 1), loc='upper left')

    plt.xticks(rotation=45)
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['font.sans-serif'] = ['SimHei']
    if vertical is not None:
        order = list(index_nav.index).index(vertical)
        plt.axvline(x=order, color='r', linestyle='--')
    plt.grid()
    plt.tight_layout()
    plt.savefig(f'{save_dir}/{title}.png')
    plt.show()


def plot_index_ret(index_ret, save_dir, title='近两周主流指数区间收益', label_size=8):
    index_ret = index_ret.sort_values(ascending=True)
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111)
    bars = ax.bar(index_ret.index, index_ret)

    # how to set label size to each bar size?

    labels = [f'{round(x * 100, 2)}%' for x in index_ret]
    ax.bar_label(bars, labels=labels, label_type='edge', fontweight='bold', color='red', fontsize=label_size)
    plt.title(title)
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.gca().yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, decimals=1))
    plt.rcParams['axes.unicode_minus'] = False
    plt.xticks(rotation=75)

    plt.tight_layout()
    plt.grid()
    plt.savefig(f'{save_dir}/{title}.png')
    plt.show()


def get_index_perf(start, end, type='债'):
    if type == '债':
        index_lst = "000012.SH,000139.SH,399307.SZ,399413.SZ"
    elif type == '股':
        index_lst = "000001.SH, 000300.SH, 000852.SH, 000905.SH"
        # index_lst = "000001.SH,000688.SH,000016.SH,000300.SH,000852.SH,399905.SZ,932000.CSI,800006.EI"
    elif type == '行业':
        index_lst = ("881002.EI,881003.EI,881004.EI,881005.EI,"
                     "881006.EI,881007.EI,881008.EI,881009.EI,881010.EI,881011.EI,881012.EI,"
                     "881013.EI,881014.EI,881015.EI,881016.EI,881017.EI,881018.EI,881019.EI,"
                     "881020.EI,881021.EI,881022.EI,881023.EI,881024.EI,881025.EI")

    else:
        raise ValueError('type must be 债 or 股 or 行业')
    index_close = get_index_close(start, end, index_lst)
    index_close = index_close.rename(
        columns={col: col.replace('东财可转债', '').replace('指数', '') for col in index_close.columns})
    index_close = index_close.rename(columns={'上证': '上证指数'})
    index_nav = get_interval_nav(index_close)
    index_ret = get_interval_ret(index_close)
    return index_nav, index_ret


def get_interval_ret(close):
    interval_ret = close.iloc[-1] / close.iloc[0] - 1
    return interval_ret


def get_interval_nav(close):
    interval_nav = close / close.iloc[0]
    return interval_nav


def get_index_close(start, end, index_lst):
    # 2024-03-08 14:46:55
    # 指数 收盘价
    data = c.csd(index_lst,
                 "CLOSE",
                 start,
                 end,
                 "period=1,adjustflag=1,curtype=1,order=1,market=CNSESH, ispandas=1")
    data = data.set_index('DATES', append=True)['CLOSE'].unstack(0)

    name = c.css(index_lst, "SHORTNAME", "ispandas=1")['SHORTNAME']
    data = data.rename(columns=name)
    data.index = pd.to_datetime(data.index)
    return data
