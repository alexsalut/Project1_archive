# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 9:03
# @Author  : Youwei Wu, Suying Zhou
# @File    : data_updater.py
# @Software: PyCharm

import os
import time
import datetime
import pandas as pd
import smtplib
import tushare as ts

from EmQuantAPI import c

from utils import c_get_trade_dates, transfer_to_jy_ticker, send_email
from fq_kline import FqKLine
from email.mime.text import MIMEText

TUSHARE_DIR = r"\\192.168.1.116\tushare\price\daily\raw"
CHOICE_DIR = "C:/Users/Yz02/Desktop/Data/Choice"
KLINE_PATH = r"\\192.168.1.116\kline\qfq_kline_product.pkl"
ST_PATH = r'\\192.168.1.116\kline\st_list.csv'
KC50_WEIGHT_DIR = r"\\192.168.1.116\choice\reference\index_weight\sh000688\cache"


def turnover_rate_update_and_confirm(today=None):
    today = time.strftime('%Y%m%d') if today is None else today
    c_download_turnover_rate_history(today, save_dir=CHOICE_DIR)
    save_path = rf'{CHOICE_DIR}/daily_turnover_rate/{today[:4]}/{today[:6]}/{today}.csv'
    subject, content = turnover_rate_email_content(save_path=save_path)
    send_email(subject, content)


def turnover_rate_email_content(save_path):
    stock_count = None
    anomaly_stock_list = None
    na_stock_list = None
    if os.path.exists(save_path):
        turnover_rate_df = pd.read_csv(save_path, index_col=0)
        subject, stock_count, anomaly_stock_list, na_stock_list = turnover_rate_check(turnover_rate_df)

    else:
        save_path = None
        subject = '[Turnover Rate] File does not exist'

    content = f""""
    Today's turnover rate info is as follows if any:
    Download path:
    {save_path}
    Number of stocks included:            {stock_count}  
    Details(Code) of stocks with missing values:
    {na_stock_list}
    Stocks with turnover rate > 100% or < 0%:
    {anomaly_stock_list}
    """
    return subject, content


def turnover_rate_check(turnover_rate_df):
    stock_count = None
    anomaly_stock_list = None
    na_stock_list = None
    if turnover_rate_df.dropna(how='all').empty:
        subject = '[Turnover Rate] File is empty'
    else:
        stock_count = len(turnover_rate_df.index)
        na_stock_list = turnover_rate_df[turnover_rate_df.isna().any(axis=1)].index.tolist()
        s = turnover_rate_df[(turnover_rate_df > 100) | (turnover_rate_df < 0)].any(axis=1)
        anomaly_stock_list = s[s].index.tolist()
        if len(anomaly_stock_list)>0:
            subject = '[Turnover Rate] File downloaded successfully with anomalous data'
        else:
            subject = '[Turnover Rate] File downloaded successfully'

    return subject, stock_count, anomaly_stock_list, na_stock_list


def c_download_turnover_rate_history(today=None, save_dir=CHOICE_DIR):
    today = time.strftime('%Y%m%d') if today is None else today
    print(f"Downloading historical turnover rate until {today}")
    print("-------------------------------------------------")

    c.start("ForceLogin=1")
    trade_dates = c.tradedates(
        "2022-06-30",
        today,
        "period=1,order=1,market=CNSESH",
    ).Dates
    c.stop()

    date_list = pd.to_datetime(trade_dates).strftime("%Y%m%d").tolist()

    for date in date_list:
        cache_dir = rf'{save_dir}/daily_turnover_rate/{date[:4]}/{date[:6]}'
        os.makedirs(cache_dir, exist_ok=True)
        save_path = os.path.join(cache_dir, f'{date}.csv')
        if os.path.exists(save_path):
            print(save_path, 'has existed.')
        else:
            c_download_daily_turnover_rate(index_ticker='001071', date=date, save_path=save_path)


def c_download_daily_turnover_rate(index_ticker, date, save_path):
    print("Downloading turnover rate")
    print("-------------------------")

    # A share market
    c.start("ForceLogin=1")
    stock_list = c.sector(index_ticker, date).Codes
    filter_list = [x for x in stock_list if x[-2:] in ['SH', 'SZ']]
    a_daily_turnover = c.css(
        filter_list,
        "TURN,FREETURNOVER",
        f"TradeDate={date}, isPandas=1",
    )
    c.stop()
    a_daily_turnover.index = transfer_to_jy_ticker(a_daily_turnover.index)
    a_daily_turnover.drop(columns=['DATES'], inplace=True)
    a_daily_turnover.to_csv(save_path)