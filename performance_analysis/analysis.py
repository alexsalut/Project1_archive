#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/18 15:59
# @Author  : Suying
# @Site    : 
# @File    : analysis.py
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from performance_analysis.data_acquisition import get_talang1_ret, get_kc_stock_pct, get_kc50_stock_list, \
    retry_get_kc50_ret
from util.send_email import Mail, R
import rqdatac as rq


def daily_performance_eval(date=None):
    formatted_date1 = time.strftime('%Y-%m-%d') if date is None else pd.to_datetime(date).strftime("%Y-%m-%d")
    data_dict = get_data(formatted_date1)
    fig_paths = []
    fig_paths.append(plot_hist_performance(data_dict['kc stock'], data_dict['talang1'], data_dict['kc50'], '科创板股票',
                                           formatted_date1))
    fig_paths.append(
        plot_hist_performance(data_dict['kc50 stock'], data_dict['talang1'], data_dict['kc50'], '科创50成分股',
                              formatted_date1))
    statistics_df = gen_statistics_table(data_dict['kc stock'], data_dict['kc50 stock'])
    notify_with_email(statistics_df, data_dict['talang1'], data_dict['kc50'], fig_paths, formatted_date1)


def notify_with_email(df_html, talang1_ret, kc50_ret, fig_paths, date=None):
    date = time.strftime('%Y-%m-%d') if date is None else pd.to_datetime(date).strftime("%Y-%m-%d")

    subject = f'[Strategy Review] {date}'
    content = f"""
    <table width="1200" border="0" cellspacing="0" cellpadding="4">
    <tr>
    <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>踏浪1号在科创板表现一览</b></td>
    </tr>
    <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
    """
    content += f"""
    <p>科创板和科创50成分股表现统计：</p>
    <center>{df_html}</center>
    <p>踏浪1号当日收益率：{format_number(talang1_ret)}</p>
    <p>科创50当日收益率：{format_number(kc50_ret)}</p>

    """
    Mail().send(
        subject,
        content,
        attachs=[],
        pics=fig_paths,
        pic_disp=['科创板涨跌幅分布', '科创50涨跌幅分布'],
        receivers=R.department['research'] + R.department['admin'],
    )


def gen_statistics_table(kc_stock_ret, kc50_stock_ret):
    kc_stock_statistics = gen_statistics(kc_stock_ret, '科创板股票')
    kc50_stock_statistics = gen_statistics(kc50_stock_ret, '科创50成分股')
    statistics_df = pd.concat([kc_stock_statistics, kc50_stock_statistics], axis=1)

    df_html = statistics_df.to_html()

    return df_html


def gen_statistics(kc_stock_ret, stock_name):
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


def format_number(value):
    if isinstance(value, int):
        return value
    elif value.is_integer():
        return int(value)
    else:
        return f'{value:.2%}'


def plot_hist_performance(kc_stock_ret, port_ret, kc50_ret, stock_name, date):
    bin_num = 100 if len(kc_stock_ret) > 1000 else 50
    plt.figure(figsize=(16, 12))
    sns.distplot(kc_stock_ret, bins=bin_num, kde=False)
    plt.title(f'{stock_name}涨跌幅分布', fontsize=25)
    plt.xlabel('涨跌幅', fontsize=15)
    plt.xticks(fontsize=15)
    plt.ylabel('计数', fontsize=15)
    plt.yticks(fontsize=15)
    plt.axvline(x=port_ret, color='r', linestyle='--', label='踏浪1号')
    plt.axvline(x=kc50_ret, color='b', linestyle='--', label='科创50指数')
    plt.axvline(x=np.mean(kc_stock_ret), color='g', linestyle='--', label=f'{stock_name}均值')
    plt.axvline(x=np.median(kc_stock_ret), color='orange', linestyle='--', label=f'{stock_name}中位数')
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.legend(fontsize=20)
    path = rf'C:\Users\Yz02\Desktop\Project_1\performance_analysis\data\{stock_name}涨跌幅分布_{date}.png'
    plt.savefig(path)
    return path


def get_data(date=None):
    rq.init()
    date = time.strftime('%Y-%m-%d') if date is None else pd.to_datetime(date).strftime("%Y-%m-%d")
    ret_dict = {
        'talang1': get_talang1_ret(date),
        'kc50': retry_get_kc50_ret(date),
        'kc stock': get_kc_stock_pct(date),
    }
    kc50_stock_list = get_kc50_stock_list(date)
    ret_dict.update({
        'kc50 stock': ret_dict['kc stock'][kc50_stock_list],
    })
    return ret_dict


if __name__ == '__main__':
    daily_performance_eval()
