#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/4/15 16:14
# @Author  : Suying
# @Site    : 
# @File    : product_indicators.py
import pandas as pd

from weekly_product_report.obtain_nav import db_connect, get_db_data



def gen_product_indicators(product, start):
    indicator_dict = {}
    nav_s = get_db_data(db_connect(), product)['cumu_netvalue2']
    nav_s[start] = 1
    nav_s = nav_s.sort_index()
    if product == 'tinglian_daily_value':
        week_s = pd.Series(index=nav_s.index, data=nav_s.index.isocalendar().week)
        year_s = pd.Series(index=nav_s.index, data=nav_s.index.isocalendar().year)
        nav_df = pd.concat([nav_s, week_s, year_s], axis=1)
        nav_s = nav_df.groupby(['year', 'week']).last()['cumu_netvalue2']
    nav_s = nav_s.sort_index()
    ret_s = nav_s.pct_change().dropna()

    indicator_dict['累计收益率'] = nav_s.iloc[-1] - 1
    indicator_dict['周均收益率'] = ret_s.mean()
    indicator_dict['周胜率'] = (ret_s>0).mean()
    indicator_dict['盈亏比'] = ret_s[ret_s>0].mean() / -ret_s[ret_s<0].mean()
    indicator_dict['正收益周'] = (ret_s>0).sum()
    indicator_dict['负收益周'] = (ret_s<0).sum()
    indicator_dict['年化收益率'] = nav_s.iloc[-1] ** (52 / (len(nav_s)-1)) - 1
    indicator_dict['最大回撤'] = (nav_s / nav_s.cummax() - 1).min()
    indicator_dict['收益回撤比'] = indicator_dict['年化收益率'] / abs(indicator_dict['最大回撤'])
    indicator_dict['夏普比率'] = indicator_dict['年化收益率'] / (ret_s.std() * (52 ** 0.5))





    indicator_s = pd.Series(indicator_dict)
    return indicator_s




if __name__ == '__main__':
    product_dict = {
        '听涟1号': 'tinglian_daily_value',
        '弄潮2号': 'nongchao2_weekly_value',
    }
    start_time = {
        '听涟1号': pd.to_datetime('2022-08-24'),
        '弄潮2号': pd.to_datetime('2023-02-06'),
    }


    data = []
    for product in product_dict.keys():
        s = gen_product_indicators(product_dict[product], start_time[product])
        s.name = product
        data.append(s)
    df = pd.concat(data, axis=1)
    df.T.to_excel('产品指标.xlsx')