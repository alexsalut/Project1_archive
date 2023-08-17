# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 9:03
# @Author  : Youwei Wu, Suying Zhou
# @File    : data_updater.py
# @Software: PyCharm

import os
import time
import pandas as pd
import tushare as ts

from utils import c_get_trade_dates, send_email


TUSHARE_DIR = r"\\192.168.1.116\tushare\price\daily\raw"
CHOICE_DIR = "C:/Users/Yz02/Desktop/Data/Choice"
KLINE_PATH = r"\\192.168.1.116\kline\qfq_kline_product.pkl"
ST_PATH = r'\\192.168.1.116\kline\st_list.csv'
KC50_WEIGHT_DIR = r"\\192.168.1.116\choice\reference\index_weight\sh000688\cache"


def raw_daily_bar_update_and_confirm(today=None):
    today = time.strftime('%Y%m%d') if today is None else today
    ts_download_raw_daily_bar_history(
        save_dir=TUSHARE_DIR,
        start_date='20220630',
        end_date=today
    )
    save_path = rf'{TUSHARE_DIR}/{today[:4]}/{today[:6]}/raw_daily_{today}.csv'
    subject, content = raw_daily_bar_email_content(save_path)
    send_email(subject, content)


def raw_daily_bar_email_content(save_path):
    if os.path.exists(save_path):
        raw_daily_bar = pd.read_csv(save_path)
        print(f'{save_path} exists.')
        subject, stock_count, na_stock = raw_daily_bar_check(raw_daily_bar)
    else:
        subject = f'[raw_daily_bar] file does not exist.'
        stock_count = 0
        na_stock = []
        save_path = None
    content = f"""
        Today's raw daily bar info is as follows if any:
    Download path:
    {save_path}
    Number of stocks included:            {stock_count}  
    Details(Code) of stocks with missing values:
    {na_stock}
    """
    return subject, content


def raw_daily_bar_check(raw_daily_bar):
    if raw_daily_bar.dropna(how='all').empty:
        subject = '[Raw Daily Bar] No data available yet.'
        save_path = None
    elif len(raw_daily_bar.index) < 5000:
        subject = '[Raw Daily Bar] Data downloaded with alert.'
    else:
        subject = '[Raw Daily Bar] Data downloaded successfully.'

    stock_count = len(raw_daily_bar.index)
    na_stock = raw_daily_bar[raw_daily_bar.isna().any(axis=1)].index.tolist()
    return subject, stock_count, na_stock


def ts_download_raw_daily_bar_history(save_dir, start_date, end_date):
    trade_dates = c_get_trade_dates(start_date, end_date)
    ts.set_token('7885a1002f5bbf605e1e5165aa56d4fcdd73325b2b94b4b863da9991')

    for date in trade_dates:
        cache_dir = rf'{save_dir}/{date[:4]}/{date[:6]}'
        os.makedirs(cache_dir, exist_ok=True)
        save_path = os.path.join(cache_dir, f'raw_daily_{date}.csv')

        if os.path.exists(save_path):
            print(save_path, 'has existed.')
        else:
            ts_download_raw_daily_bar(save_path, date)


def ts_download_raw_daily_bar(save_path, date):
    """
    Returns
    -------
    daily_bar: pd.DataFrame

        名称	类型	描述
        ts_code	str	股票代码
        trade_date	str	交易日期
        open	float	开盘价
        high    float	最高价
        low     float	最低价
        close	float	收盘价
        pre_close	float	昨收价(前复权)
        change	float	涨跌额
        pct_chg	float	涨跌幅
        vol	    float	成交量 （手）
        amount	float	成交额 （千元）
    """
    pro = ts.pro_api()
    raw_daily_bar = pro.daily(trade_date=date).set_index('ts_code')
    raw_daily_bar = raw_daily_bar.loc[raw_daily_bar.index.str[-2:] != 'BJ']
    raw_daily_bar.to_csv(save_path)
    print(save_path, 'has downloaded.')