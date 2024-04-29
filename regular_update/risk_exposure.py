# -*- coding: utf-8 -*-
# @Time    : 2023/6/13 16:09
# @Author  : Youwei Wu
# @File    : risk_exposure.py
# @Software: PyCharm
import os.path
import time
import rqdatac as rq

import pandas as pd

from util.send_email import Mail, R
from util.file_location import FileLocation
from rice_quant.exposure_plot import plot_all_barra_expo



exposure_save_dir = FileLocation.exposure_dir
rq.init()

def send_risk_exposure(date=None):
    formatted_date = time.strftime('%Y%m%d') if date is None else pd.to_datetime(date).strftime('%Y%m%d')
    expo_df = gen_expo_df(formatted_date)
    barra_txt = gen_barra_txt(expo_df)
    industry_txt = gen_industry_txt(expo_df)
    send_expo_email(formatted_date, barra_txt, industry_txt)


def gen_expo_df(formatted_date):
    # funds = ['踏浪1号', '踏浪2号', '踏浪3号']
    funds = ['踏浪1号', '踏浪2号']
    trading_dates = rq.get_trading_dates('20231001',formatted_date)
    trading_dates = [x.strftime('%Y%m%d') for x in trading_dates]
    for date in trading_dates:
        path = fr'{exposure_save_dir}\expo_{date}.csv'
        if os.path.exists(path):
            print(f'Risk exposure file for {date} already exists')
        else:
            data = [get_port_excess_exposure(date=date, fund=x) for x in funds]
            expo_df = pd.concat(data, axis=1, keys=funds)
            expo_df.to_csv(fr'{exposure_save_dir}\expo_{date}.csv', encoding='gbk')
            print(f'Risk exposure file for {date} generated')
            if date == formatted_date:
                return expo_df


def gen_barra_txt(expo_df):
    barra_df = expo_df.iloc[:11]
    styled_barra_df = barra_df.style.bar(
        # subset=[('踏浪1号', 'relative'), ('踏浪2号', 'relative'), ('踏浪3号', 'relative')],
        subset=[('踏浪1号', 'relative'), ('踏浪2号', 'relative')],
        color='#d65f5f',
    )
    styled_barra_df = styled_barra_df.format('{:.2f}')
    barra_text = styled_barra_df.to_html(float_format='%.2f')
    return barra_text


def gen_industry_txt(expo_df):
    industry_df = expo_df.iloc[11:]
    styled_industry_df = industry_df.style.bar(
        # subset=[('踏浪1号', 'relative'), ('踏浪2号', 'relative'), ('踏浪3号', 'relative')],
        subset=[('踏浪1号', 'relative'), ('踏浪2号', 'relative')],
        color='#d65f5f',
    )

    styled_industry_df = styled_industry_df.format('{:.2f}')
    industry_text = styled_industry_df.to_html(float_format='%.2f')
    industry_text = industry_text.replace('nan', '-')
    return industry_text


def send_expo_email(formatted_date, barra_txt, industry_txt):
    file_list = plot_all_barra_expo(date=formatted_date)
    Mail().send(
        subject=f'[Risk Exposure] File generated for {formatted_date}',
        body_content=fr"""
            <table width="800" border="0" cellspacing="0" cellpadding="4">
            <tr>
            <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>Exposure file generated</b></td>
            </tr>
            <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
            <p>文件路径:</p>
            {exposure_save_dir}\expo_{formatted_date}.csv <p>Barra及仓位因子暴露：</p> 
            <html><head><style>table.bordered-table {{ border-collapse: seperate; width: 100%; }} 
            table.bordered-table, th, td {{ border: 1px solid black; }} th, td {{ padding: 8px;}}</style> 
            </head><body>{barra_txt}</body></html> 

             <p>行业因子暴露：</p> <html><head><style>table.bordered-table {{ border-collapse: seperate; width: 100%; }} 
             table.bordered-table, th, td {{ border: 1px solid black; }} th, td {{ padding: 8px;}} th, td {{ width: 
             50%; }} </style></head><body>{industry_txt}</body></html> 
            """,
        attachs=file_list,
        receivers=R.department['research'] + R.department['admin'],
    )


def get_port_excess_exposure(date, fund):
    print(fund)
    port_weight = get_port_weight(date=date, fund=fund)
    port_exposure = get_port_exposure(date, port_weight)
    index_exposure = get_index_exposure(date, fund)
    relative_exposure = port_exposure - index_exposure
    expo_df = pd.concat([port_exposure, index_exposure, relative_exposure],
                        axis=1,
                        keys=['port', index_exposure.name, 'relative'])

    expo_df[(expo_df == 0).all(axis=1)] = None
    return expo_df


def get_port_weight(date, fund):
    if fund == '踏浪1号':
        new_date = pd.to_datetime(date).strftime('%Y-%m-%d')
        pos_df = pd.read_csv(fr'\\192.168.1.116\trade\broker\cats\account/CreditPosition_{new_date}.csv')
        pos_s = pos_df.query("备注 == '踏浪1信用账户' & 当前余额 > 0").set_index('代码')['参考市值']
        stocklist = pos_s.index.astype(str) + '.XSHG'
        port_weight = pos_s / pos_s.sum()
        port_weight.index = stocklist
    else:
        pos_df = get_pos_df(date=date, fund=fund)
        stock_pos_df = pos_df.query('证券代码.str.startswith("6") | 证券代码.str.startswith("0") | 证券代码.str.startswith("3")')
        stock_pos_df['市值占比'] = stock_pos_df['市值'] / stock_pos_df['市值'].sum()
        stocklist = stock_pos_df['证券代码'] + '.' + stock_pos_df['市场代码'].replace('SH', 'XSHG').replace('SZ', 'XSHE')
        port_weight = stock_pos_df['市值占比']
        port_weight.index = stocklist
    return port_weight


def get_port_exposure(date, port_weight):
    port_weight = port_weight[~port_weight.index.str.startswith('5')]
    if len(port_weight) == 0:
        return pd.Series()
    rq_exposure = rq.get_factor_exposure(
        order_book_ids=port_weight.index,
        start_date=date,
        end_date=date,
        factors=None,
        industry_mapping='sw2021',
    )
    if rq_exposure is None:
        print(f'[{time.strftime("%x %X")}] '
              f'RiceQuant has no risk-exposure data({date}) yet, retry in 10 min.')
        time.sleep(600)
        return get_port_exposure(date, port_weight)

    else:
        stock_exposure = rq_exposure.reset_index('date', drop=True)
        portfolio_exposure = stock_exposure.mul(port_weight, axis=0).sum()
        return portfolio_exposure


def get_index_exposure(date, fund):
    if fund == '踏浪2号':
        index_ticker = '000905.XSHG'
    elif fund == '踏浪3号':
        index_ticker = '000852.XSHG'
    elif fund == '踏浪1号':
        index_ticker = '000688.XSHG'
    else:
        raise

    index_exposure = rq_get_index_exposure(date, index_ticker)
    if index_exposure is None:
        print(f'[{time.strftime("%x %X")}] '
              f'RiceQuant has no risk-exposure data({date}) yet, retry in 10 min.')
        time.sleep(5)
        index_exposure = get_index_exposure(date, fund)
    return index_exposure


def get_pos_df(date, fund):
    if fund == '踏浪2号':
        subdir = 'qmt_ha'
    elif fund == '踏浪3号':
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
    index_weight = rq.index_weights(index_ticker, date=date)
    index_comp_exposure = rq.get_factor_exposure(
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
    # get_port_excess_exposure('20240326', '踏浪3号')
    send_risk_exposure('20240424')