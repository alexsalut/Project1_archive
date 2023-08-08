# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 9:03
# @Author  : Youwei Wu
# @File    : data_updater.py
# @Software: PyCharm

import os
import time

import tushare as ts
from EmQuantAPI import c
from utils import c_get_trade_dates, transfer_to_jy_ticker

# from script.preprocess.fq_kline import FqKLine
# from script.product.utils import ProductPath, c_get_trade_dates, transfer_to_jy_ticker

TUSHARE_PATH = "C：/Users/Yz02/Desktop/Tushare"


def update_adjusted_kline():
    FqKLine(
        tushare_dir=TUSHARE_PATH,
        save_path=TUSHARE_PATH,
    ).gen_qfq_kline()


def ts_download_raw_daily_bar(today=None):
    today = time.strftime('%Y%m%d') if today is None else today
    ts_download_history(
        start_date='20221231',
        end_date=today,
        save_dir=TUSHARE_PATH,
    )


def ts_download_history(start_date, end_date, save_dir):
    trade_dates = c_get_trade_dates(start_date, end_date)
    ts.set_token('7885a1002f5bbf605e1e5165aa56d4fcdd73325b2b94b4b863da9991')

    for date in trade_dates:
        cache_path = rf'{save_dir}/{date[:4]}/{date[:6]}'
        os.makedirs(cache_path, exist_ok=True)
        save_path = os.path.join(cache_path, f'raw_daily_{date}.csv')

        if os.path.exists(save_path):
            print(save_path, 'has existed.')
        else:
            ts_download_daily(date, save_path)


def ts_download_daily(date, save_path):
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
    daily_bar = pro.daily(trade_date=date).set_index('ts_code')
    if daily_bar.empty:
        print('No data:', date)
    else:
        daily_bar = daily_bar.loc[daily_bar.index.str[-2:] != 'BJ']
        daily_bar.to_csv(save_path)
        print(save_path, 'has downloaded.')


def c_download_kc50_index_weight(date):
    c_download_index_weight(index_ticker='000688.SH', date=date)


def c_download_index_weight(index_ticker, date):
    print("Downloading Index Composition Weight")
    print("-----------------------------------")
    jy_ticker = transfer_to_jy_ticker([index_ticker])[0]

    c.start()
    df = c.ctr(
        "INDEXCOMPOSITION",
        "SECUCODE,WEIGHT",
        f"IndexCode={index_ticker},EndDate={date},ispandas=1",
    )
    c.stop()
    cache_dir = rf'E:\choice\reference\index_weight\{jy_ticker}/cache'
    df.to_pickle(rf'{cache_dir}/{date}.pkl')


if __name__ == '__main__':
    ts_download_raw_daily_bar()
