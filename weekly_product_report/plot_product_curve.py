#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/4/8 10:31
# @Author  : Suying
# @Site    : 
# @File    : plot_product_curve.py
import matplotlib.pyplot as plt
import rqdatac as rq
from weekly_product_report.gen_stats import ProductStats


def plot_product_curve(product):
    p = ProductStats()
    product_index_code_dict = p.index_code_dict
    product_start_date = p.start_date[product].strftime('%Y%m%d')

    rq.init()
    nav_dict = p.get_nav_history()
    product_df = nav_dict[product]
    product_weekly_nav = product_df['cumu_netvalue2'].loc[product_start_date:]
    weekly_ret = product_weekly_nav.pct_change().dropna()
    start = product_weekly_nav.index[0].strftime('%Y%m%d')
    end = product_weekly_nav.index[-1].strftime('%Y%m%d')

    fig, ax = plt.subplots(figsize=(12, 6))
    product_weekly_nav.plot(ax=ax, label=product, legend=True, color='#e4342c', linewidth=2)

    if product in product_index_code_dict.keys():
        product_index_code = product_index_code_dict[product]
        code = rq.id_convert(product_index_code)
        index = rq.get_price(code, start_date=start, end_date=end, fields='close').droplevel(0)['close']
        index_weekly_nav = index.loc[product_weekly_nav.index]
        index_weekly_nav /= index_weekly_nav.iloc[0]
        excess_nav = product_weekly_nav / index_weekly_nav
        excess_ret = excess_nav.pct_change().dropna()
        excess_std = excess_ret.std() * (52 ** 0.5)

        index_weekly_nav.plot(ax=ax, label=product_index_code, legend=True, color='#71b5fc', linewidth=2)
        excess_nav.plot(ax=ax, label='超额收益（几何）', legend=True, color='#ffb300', linewidth=2)
        plt.text(x=excess_nav.index[1], y=0.9, s=f'年化超额波动率：{excess_std:.2%}', fontsize=12, ha='left')

    ret_std = weekly_ret.std() * (52 ** 0.5)

    plt.xlabel('日期')
    plt.grid()
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.title(f'{product}历史净值')

    plt.text(x=weekly_ret.index[1], y=0.87, s=f'年化波动率：{ret_std:.2%}', fontsize=12, ha='left')
    plt.savefig(f'{product}历史净值.png')
    plt.show()
