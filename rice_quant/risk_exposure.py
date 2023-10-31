# -*- coding: utf-8 -*-
# @Time    : 2023/6/13 16:09
# @Author  : Youwei Wu
# @File    : risk_exposure.py
# @Software: PyCharm
import os.path
import time
import rqdatac

import pandas as pd

from util.utils import send_email, SendEmailInfo
from file_location import FileLocation as FL
from rice_quant.exposure_plot import plot_all_barra_expo
from util.send_email import Mail, R

rqdatac.init()

exposure_save_dir = FL().exposure_dir


def gen_expo_df(date):
    formatted_date = pd.to_datetime(date).strftime('%Y%m%d')
    products = ['talang2', 'talang3', 'panlan']
    data = []

    try:
        for p in products:
            print(p)
            data.append(get_port_excess_exposure(date=formatted_date, product=p))
        expo_df = pd.concat(data, axis=1, keys=products)
        expo_df.to_csv(fr'{exposure_save_dir}\expo_{formatted_date}.csv', encoding='gbk')

        file_list = plot_all_barra_expo(date=formatted_date)

        barra_df = expo_df.iloc[:11]
        styled_barra_df = barra_df.style.bar(
            subset=[('talang2', 'relative'), ('talang3', 'relative'), ('panlan', 'relative')],
            color='#d65f5f',
        )
        styled_barra_df = styled_barra_df.format('{:.2f}')
        barra_text = styled_barra_df.to_html(float_format='%.2f')

        industry_df = expo_df.iloc[11:]
        styled_industry_df = industry_df.style.bar(
            subset=[('talang2', 'relative'), ('talang3', 'relative'), ('panlan', 'relative')],
            color='#d65f5f',
        )
        styled_industry_df = styled_industry_df.format('{:.2f}')
        industry_text = styled_industry_df.to_html(float_format='%.2f')
        print(fr'[Strategy Exposure] File generated for {date}')
        Mail().send(
            subject=f'[Strategy Exposure] File generated for {date}',
            body_content=fr"""
                <table width="800" border="0" cellspacing="0" cellpadding="4">
                <tr>
                <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>Exposure file generated</b></td>
                </tr>
                <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
                <p>文件路径:</p>
                {exposure_save_dir}\expo_{date}.csv
                <p>Barra及仓位因子暴露：</p>
                <html><head><style>table.bordered-table
                {{ border-collapse: seperate; width: 100%; }} table.bordered-table, th, td {{ border: 1px solid black; }} th, td {{ padding: 8px;}}</style>
                </head><body>{barra_text}</body></html>

                 <p>行业因子暴露：</p>
                <html><head><style>table.bordered-table
                {{ border-collapse: seperate; width: 100%; }} table.bordered-table, th, td {{ border: 1px solid black; }} th, td {{ padding: 8px;}}
                th, td {{ width: 50%; }}
                </style></head><body>{industry_text}</body></html>
                """,
            attachs=file_list,
            receivers=R.department['research'] + R.department['admin'],

        )
    except Exception as e:
        print(e)
        print(f'Error in gen_expo_df, retry in 5 minutes')
        time.sleep(300)
        gen_expo_df(date=date)


def get_port_excess_exposure(date, product):
    port_exposure = get_port_exposure(date, product)
    index_exposure = get_index_exposure(date, product)
    relative_exposure = port_exposure - index_exposure
    expo_df = pd.concat([port_exposure, index_exposure, relative_exposure],
                        axis=1,
                        keys=['port', index_exposure.name, 'relative'])
    return expo_df


def get_port_exposure(date, product):
    if product == 'panlan':
        new_date = pd.to_datetime(date).strftime('%Y-%m-%d')
        pos_s = pd.read_csv(fr'\\192.168.1.116\trade\broker\cats\account/StockPosition_{new_date}.csv', index_col=2)[
            '参考市值']
        stocklist = pos_s.index.astype(str) + '.XSHG'
        weight = pos_s / pos_s.sum()
        weight.index = stocklist
    else:
        pos_df = get_pos_df(date=date, product=product)
        stocklist = pos_df['证券代码'] + '.' + pos_df['市场代码'].replace('SH', 'XSHG').replace('SZ', 'XSHE')
        weight = pos_df['市值占比'].str[:-1].astype(float) / 100  # 还有个资产占比
        weight.index = stocklist

    stock_exposure = rqdatac.get_factor_exposure(
        stocklist,
        date,
        date,
        factors=None,
        industry_mapping='sw2021',
    ).reset_index('date', drop=True)

    portfolio_exposure = stock_exposure.mul(weight, axis=0).sum()
    return portfolio_exposure


def get_index_exposure(date, product):
    if product == 'talang2':
        index_ticker = '000905.XSHG'
    elif product == 'talang3':
        index_ticker = '000852.XSHG'
    elif product == 'panlan':
        index_ticker = '000688.XSHG'
    else:
        raise

    index_exposure = rq_get_index_exposure(date, index_ticker)
    return index_exposure


def get_pos_df(date, product):
    if product == 'talang2':
        subdir = 'qmt_gf'
    elif product == 'talang3':
        subdir = 'iQuant'
    else:
        raise

    pos_df = pd.read_csv(
        rf"\\192.168.1.116\trade\broker\{subdir}\account\Stock/PositionStatics-{date}.csv",
        encoding='gbk',
        converters={'证券代码': str},
    ).query("市值>0")
    return pos_df


def rq_get_index_exposure(date, index_ticker):
    index_weight = rqdatac.index_weights(index_ticker, date=date)
    index_comp_exposure = rqdatac.get_factor_exposure(
        index_weight.index,
        date,
        date,
        factors=None,
        industry_mapping='sw2021',
    ).reset_index('date', drop=True)
    index_exposure = index_comp_exposure.mul(index_weight, axis=0).sum()
    index_exposure.name = index_ticker
    return index_exposure


if __name__ == '__main__':
    gen_expo_df('20231030')
