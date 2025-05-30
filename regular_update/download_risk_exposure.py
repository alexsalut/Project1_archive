# -*- coding: utf-8 -*-
# @Time    : 2023/6/13 16:09
# @Author  : Youwei Wu
# @File    : download_risk_exposure.py
# @Software: PyCharm
import os.path
import time
import rqdatac as rq

import pandas as pd

from util.send_email import Mail, R
from util.file_location import FileLocation
from rice_quant.exposure_plot import plot_all_barra_expo
from regular_update.position_check import AccountPosition

exposure_save_dir = FileLocation.exposure_dir

def download_history_market_exposure(end, start='20240101'):
    rq.init()
    trading_dates = rq.get_trading_dates(start, end)
    for date in trading_dates:
        download_daily_market_exposure(date)


def download_daily_market_exposure(date=None):
    date = time.strftime('%Y%m%d') if date is None else pd.to_datetime(date).strftime('%Y%m%d')
    bar_path = rf'{FileLocation.raw_daily_dir}/{date[:4]}/{date[:6]}/raw_daily_{date}.csv'

    save_dir = r'D:\data\archive\factor\barra'
    save_path = rf'{save_dir}\{date}.csv'
    # save_path = rf'\\192.168.1.116\data\factor\barra\{date}.csv'

    if os.path.exists(save_path):
        print(f'Risk exposure file for {date} already exists')
    else:
        df = pd.read_csv(bar_path, index_col=0)
        stock_list = df.index.tolist()
        stock_list = rq.id_convert(stock_list)

        index_comp_exposure = rq.get_factor_exposure(
            stock_list,
            date,
            date,
            factors=None,
            industry_mapping='sw2021',
        )

        if index_comp_exposure is None:
            print(f'RiceQuant has no risk-exposure data({date}) ')
        else:
            index_comp_exposure = index_comp_exposure.reset_index('date', drop=True)
            barra = index_comp_exposure.loc[:, : 'comovement']
            industry = index_comp_exposure.loc[:, '银行':]
            industry = industry.stack().reset_index(1)

            industry = industry.rename(columns={'level_1': 'industry', 0: 'relative'})
            industry = industry.query('relative != 0')

            df = pd.concat([barra, industry['industry']], axis=1)
            del df['comovement']
            df.to_csv(save_path, encoding='gbk')
            print(f'Risk exposure file for {date} generated')


def send_risk_exposure(date=None):
    rq.init()
    formatted_date = time.strftime('%Y%m%d') if date is None else pd.to_datetime(date).strftime('%Y%m%d')
    expo_df = gen_expo_df(formatted_date)
    barra_txt = gen_barra_txt(expo_df)
    industry_txt = gen_industry_txt(expo_df)
    send_expo_email(formatted_date, barra_txt, industry_txt)


def gen_expo_df(formatted_date):
    funds = ['踏浪1号', '踏浪2号', '踏浪3号']
    # funds = ['踏浪1号', '踏浪2号']
    trading_dates = rq.get_trading_dates('20231001', formatted_date)
    trading_dates = [x.strftime('%Y%m%d') for x in trading_dates]
    for date in trading_dates:
        path = fr'{exposure_save_dir}\expo_{date}.csv'
        if os.path.exists(path):
            print(f'Risk exposure file for {date} already exists')
            expo_df = pd.read_csv(path, encoding='gbk', header=[0, 1], index_col=0)
            if date == formatted_date:
                return expo_df
        else:
            data = [get_port_excess_exposure(date=date, fund=x) for x in funds]
            expo_df = pd.concat(data, axis=1, keys=funds)
            expo_df.to_csv(fr'{exposure_save_dir}\expo_{date}.csv', encoding='gbk')
            print(f'Risk exposure file for {date} generated')
            if date == formatted_date:
                expo_df = pd.read_csv(path, encoding='gbk', header=[0, 1], index_col=0)
                return expo_df


def gen_barra_txt(expo_df):
    barra_df = expo_df.iloc[:11]
    styled_barra_df = barra_df.style.bar(
        subset=[('踏浪1号', 'relative'), ('踏浪2号', 'relative'), ('踏浪3号', 'relative')],
        # subset=[('踏浪1号', 'relative'), ('踏浪2号', 'relative')],
        color='#d65f5f',
    )
    styled_barra_df = styled_barra_df.format('{:.2f}')
    barra_text = styled_barra_df.to_html(float_format='%.2f')
    return barra_text


def gen_industry_txt(expo_df):
    industry_df = expo_df.iloc[11:]
    styled_industry_df = industry_df.style.bar(
        subset=[('踏浪1号', 'relative'), ('踏浪2号', 'relative'), ('踏浪3号', 'relative')],
        # subset=[('踏浪1号', 'relative'), ('踏浪2号', 'relative')],
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
    pos_df = AccountPosition(fund, date).get_actual_position()
    pos_s = pos_df['市值']
    stock_conversion = lambda x: x + '.XSHG' if x.startswith('6') else x + '.XSHE'
    stocklist = [stock_conversion(x) for x in pos_s.index]
    port_weight = pos_s / pos_s.sum()
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
        index_ticker = '000905.XSHG'
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
