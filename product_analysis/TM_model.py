#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/4/8 10:46
# @Author  : Suying
# @Site    : 
# @File    : TM_model.py

import pandas as pd
import numpy as np
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import rqdatac as rq
import statsmodels.api as sm
import xlwings as xw

def get_all_product_TM_model(start_date='2022-01-01', end_date='2023-12-31'):
    product_weekly_ret, index_weekly_ret, annual_excess_ret, ir = read_file(start_date, end_date)
    rf = 0
    data = []
    for product in product_weekly_ret.columns:
        y = product_weekly_ret[product] - rf
        x = index_weekly_ret - rf
        X = pd.concat([x.rename('线性'), (x ** 2).rename('择时')], axis=1)
        X = sm.add_constant(X).rename(columns={'const': '选股'})
        model = sm.OLS(y, X).fit()
        t = (model.tvalues).rename('t值')
        p = (model.pvalues).rename('p值')
        coeff = (model.params).rename('系数')
        result = pd.concat([coeff, t, p], axis=1)
        result = result.loc[['选股', '择时']].stack().rename(product)
        data.append(result)
    result = pd.concat(data, axis=1).T
    all_result = pd.concat([result, annual_excess_ret, ir], axis=1)
    all_result = all_result.round(3)
    all_result.index.name = '产品'
    all_result.to_excel(f'500指增产品TM模型分析{start_date}_{end_date}.xlsx')


def read_file(start_date='2022-01-01', end_date='2023-12-31'):
    rq.init()
    path = r'C:\Users\Yz02\Desktop\Data\净值数据-500指增.xlsx'
    df = pd.read_excel(path, sheet_name='复权净值', index_col=0, header=0)
    df_22 = df[df.index >= start_date]
    df_22 = df_22[df_22.index <= end_date].sort_index()


    start = df_22.index[0]
    end = df_22.index[-1]
    index_price = rq.get_price('000905.XSHG',
                               start_date=start,
                               end_date=end,
                               fields='close').droplevel(0)['close']

    price_df = pd.concat([df_22, index_price.rename('指数')], axis=1)
    price_weekly = price_df.resample('W').last().ffill()

    nav_weekly = price_weekly.div(price_weekly.iloc[0])
    index_nav = nav_weekly['指数']
    del nav_weekly['指数']
    excess_nav = nav_weekly.div(index_nav, axis=0)



    # plot_nav(excess_nav, start=start.strftime('%Y%m%d'), end=end.strftime('%Y%m%d'))
    #



    annual_excess_ret = excess_nav.iloc[-1] ** (52 / (len(excess_nav)-1)) - 1
    annual_excess_ret = annual_excess_ret.rename('年化超额收益率')
    ir = annual_excess_ret / (excess_nav.pct_change().std() * (52 ** 0.5))
    ir = ir.rename('信息比率')

    index_weekly_ret = index_nav.pct_change().dropna()
    product_weekly_ret = nav_weekly.pct_change().dropna()
    return product_weekly_ret, index_weekly_ret, annual_excess_ret, ir


def plot_nav(df, start, end):
    df /= df.iloc[0]
    last_nav = df.iloc[-1]
    last_nav = last_nav.sort_values(ascending=False)
    df = df[last_nav.index]
    plt.figure(figsize=(12, 6))
    for col in df.columns:
        plt.plot(df[col], label=col)
    plt.title('各500指增产品超额净值走势图')
    plt.legend()
    plt.xlabel('日期')
    plt.ylabel('超额净值')
    plt.grid()
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.rcParams['axes.unicode_minus'] = False
    plt.tight_layout()
    plt.savefig(f'各500指增产品超额净值走势图{start}_{end}.png')
    plt.show()


if __name__ == '__main__':
    get_all_product_TM_model(start_date='2023-01-01', end_date='2023-12-31')