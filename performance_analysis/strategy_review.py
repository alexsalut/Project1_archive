#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/18 15:59
# @Author  : Suying
# @Site    : 
# @File    : strategy_review.py

import time

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import rqdatac as rq

from util.send_email import Mail, R
from performance_analysis.data_acquisition import \
    get_talang1_ret, get_kc_stock_pct, get_kc50_stock_list, rq_retry_get_kc50_ret


def send_strategy_review(date=None):
    date = time.strftime('%Y-%m-%d') if date is None else pd.to_datetime(date).strftime('%Y-%m-%d')
    rq.init()
    start_day = rq.get_previous_trading_date(date, 21)
    trading_days = rq.get_trading_dates(start_day, date)
    trading_days = [date.strftime('%Y-%m-%d') for date in trading_days]
    data = get_history_data(trading_days)
    nav_df, ret_df = get_market_performance(data)

    fig_paths = [plot_hist_performance(data[trading_days[-1]], stock_name=x)
                 for x in ['科创板股票', '科创50成分股']]
    fig_paths.append(plot_market_bar_ret(ret_df))
    fig_paths.append(plot_market_nav(nav_df))
    statistics_df = gen_statistics_table(data[date])
    notify_with_email(
        df_html=statistics_df,
        data_dict=data[date],
        fig_paths=fig_paths,
        date = date
    )


def get_market_performance(data):
    kc50_medians = pd.Series([x['科创50中位数'] for x in data.values()], index=data.keys(),name='科创50中位数')
    kc50_median_nav = kc50_medians.cumsum() + 1
    kc50_median_nav /= kc50_median_nav.iloc[0]
    kc_medians = pd.Series([x['科创板中位数'] for x in data.values()], index=data.keys(), name='科创板中位数')
    kc_median_nav = kc_medians.cumsum() + 1
    kc_median_nav /= kc_median_nav.iloc[0]

    diff = (kc_medians - kc50_medians).rename('科创板-科创50')
    diff_nav = diff.cumsum() + 1
    diff_nav /= diff_nav.iloc[0]
    return pd.concat([kc50_median_nav, kc_median_nav, diff_nav], axis=1), pd.concat([kc50_medians, kc_medians], axis=1)

def plot_market_nav(nav_df):
    fig, ax = plt.subplots(figsize=(13, 10))
    plt.plot(nav_df['科创50中位数'], marker='o', color='blue', linestyle='--')
    plt.plot(nav_df['科创板中位数'], marker='o', color='red', linestyle='--')
    plt.plot(nav_df['科创板-科创50'], marker='o', color='orange')
    plt.title('科创板和科创50中位数净值表现', fontsize=20)
    plt.xlabel('日期', fontsize=15)
    plt.xticks(fontsize=10, rotation=45)
    plt.ylabel('净值', fontsize=15)
    plt.yticks(fontsize=15)
    plt.grid()
    plt.legend(fontsize=15)
    plt.legend(['科创50中位数', '科创板中位数', '科创板-科创50'], fontsize=20)
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.tight_layout()


    nav_path = rf'Z:\temp\performance_analysis\data\科创中位数净值_{nav_df.index[-1]}.png'
    plt.savefig(nav_path)
    plt.show()
    return nav_path

def plot_market_bar_ret(ret_df):
    plt.figure(figsize=(16, 12))
    ret_df.plot(kind='bar', figsize=(16, 12))
    plt.title('科创板和科创50中位数收益率', fontsize=25)
    plt.xlabel('日期', fontsize=20)
    plt.xticks(fontsize=10, rotation=45)
    plt.ylabel('日收益率', fontsize=20)
    plt.yticks(fontsize=20)
    plt.grid()

    plt.legend(fontsize=20)
    plt.legend(['科创50中位数', '科创板中位数'], fontsize=20)
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.tight_layout()
    ret_path = rf'Z:\temp\performance_analysis\data\科创中位数日收益率_{ret_df.index[-1]}.png'
    plt.savefig(ret_path)
    plt.show()
    return ret_path



def get_history_data(dates):
    data = {}
    for date in dates:
        data[date] = get_data_dict(date)
    return data


def get_data_dict(date):
    if date is None:
        date = time.strftime('%Y-%m-%d')
    else:
        date = pd.to_datetime(date).strftime("%Y-%m-%d")

    kc50_stock_list = get_kc50_stock_list(date)

    kc_stock_ret = get_kc_stock_pct(date)
    kc50_stock_ret = kc_stock_ret[kc50_stock_list]


    ret_dict = {
        'date': date,
        'talang1': get_talang1_ret(date),
        'kc50_index': rq_retry_get_kc50_ret(date),
        '科创板股票': kc_stock_ret,
        '科创板中位数': np.median(kc_stock_ret.values),
        '科创50成分股': kc50_stock_ret,
        '科创50中位数': np.median(kc50_stock_ret.values),
    }
    return ret_dict





def plot_hist_performance(data_dict, stock_name):
    kc_stock_ret = data_dict[stock_name]

    plt.figure(figsize=(16, 12))
    bin_num = 100 if len(kc_stock_ret) > 1000 else 50
    sns.distplot(kc_stock_ret, bins=bin_num, kde=False)
    plt.title(f'{stock_name}涨跌幅分布', fontsize=25)
    plt.xlabel('涨跌幅', fontsize=20)
    plt.xticks(fontsize=20)
    plt.ylabel('计数', fontsize=20)
    plt.yticks(fontsize=20)
    plt.axvline(x=np.mean(kc_stock_ret), color='g', linestyle='--', linewidth=3, label=f'{stock_name}均值')
    plt.axvline(x=np.median(kc_stock_ret), color='orange', linestyle='--', linewidth=3, label=f'{stock_name}中位数')
    plt.axvline(x=data_dict['kc50_index'], color='b', linestyle='--', linewidth=4, label='科创50指数')
    plt.axvline(x=data_dict['talang1'], color='r', linestyle='--', linewidth=4, label='踏浪1号')
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.legend(fontsize=20)

    path = rf'Z:\temp\performance_analysis\data\{stock_name}涨跌幅分布_{data_dict["date"]}.png'
    plt.savefig(path)
    return path


def gen_statistics_table(data_dict):
    data = [gen_statistics(data_dict, x) for x in ['科创板股票', '科创50成分股']]
    statistics_df = pd.concat(data, axis=1)
    df_html = statistics_df.to_html()
    return df_html


def gen_statistics(data_dict, stock_name):
    kc_stock_ret = data_dict[stock_name]
    statistics_s = pd.Series(data={
        '上涨数': len(kc_stock_ret[kc_stock_ret > 0]),
        '下跌数': len(kc_stock_ret[kc_stock_ret < 0]),
        '持平数': len(kc_stock_ret[kc_stock_ret == 0]),
        '上涨比例': len(kc_stock_ret[kc_stock_ret > 0]) / len(kc_stock_ret),
        '均值': np.mean(kc_stock_ret),
        '中位数': np.median(kc_stock_ret),
        '标准差': np.std(kc_stock_ret),
        '最大值': np.max(kc_stock_ret),
        '最小值': np.min(kc_stock_ret),
    }, name=stock_name)
    statistics_s = statistics_s.apply(format_number)
    return statistics_s


def notify_with_email(df_html, data_dict, fig_paths, date):
    subject = f'[Strategy Review] {data_dict["date"]}'
    content = f"""
    <table width="1200" border="0" cellspacing="0" cellpadding="4">
    <tr>
    <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>踏浪1号在科创板表现一览</b></td>
    </tr>
    <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
    
    <p>科创板股票和科创50成分股表现统计：</p>
    <center>{df_html}</center>
    <p>踏浪1号当日收益率：{format_number(data_dict["talang1"])}</p>
    <p>科创50指数当日收益率：{format_number(data_dict["kc50_index"])}</p>
    """

    monitor_dir = r'\\192.168.1.116\target_position\monitor'
    formatted_date1 = pd.to_datetime(date).strftime('%Y%m%d')
    formatted_date2 = pd.to_datetime(date).strftime('%Y-%m-%d')
    path1 = rf'{monitor_dir}\monitor_{formatted_date1}.xlsx'
    path2 = rf'{monitor_dir}\monitor_zz500_{formatted_date2}.xlsx'


    Mail().send(
        subject,
        content,
        attachs=[path1, path2],
        pics=fig_paths,
        pic_disp=['科创板涨跌幅分布', '科创50涨跌幅分布', '科创板和科创50中位数收益率', '科创板和科创50中位数净值表现'],
        receivers=R.department['research'] + R.department['admin'],
    )


def format_number(value):
    if isinstance(value, int):
        return value
    elif value.is_integer():
        return int(value)
    else:
        return f'{value:.2%}'


if __name__ == '__main__':
    send_strategy_review('20240409')