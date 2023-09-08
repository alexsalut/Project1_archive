# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 9:03
# @Author  : Youwei Wu, Suying Zhou
# @File    : data_updater.py
# @Software: PyCharm

import os
import time
import pandas as pd
import tushare as ts
import rqdatac

from EmQuantAPI import c
from utils import c_get_trade_dates, send_email, send_email_with_alert

TUSHARE_DIR = r"\\192.168.1.116\tushare\price\daily\raw"
CHOICE_DIR = "C:/Users/Yz02/Desktop/Data/Choice"
KLINE_PATH = r"\\192.168.1.116\kline\qfq_kline_product.pkl"
ST_PATH = r'\\192.168.1.116\kline\st_list.csv'
KC50_WEIGHT_DIR = r"\\192.168.1.116\choice\reference\index_weight\sh000688\cache"


class RawDailyBarUpdater:
    def __init__(self,today=None):
        self.save_dir = TUSHARE_DIR

    def update_and_confirm_raw_daily_bar(self, today=None):
        today = time.strftime('%Y%m%d') if today is None else today
        self.ts_download_raw_daily_bar_history(
            start_date='20220630',
            end_date=today,
        )
        tushare_path = rf'{TUSHARE_DIR}/{today[:4]}/{today[:6]}/raw_daily_{today}.csv'
        self.retry_download_check(tushare_path=tushare_path,date=today)


    def ts_download_raw_daily_bar_history(self, start_date, end_date):
        trade_dates = c_get_trade_dates(start_date, end_date)
        ts.set_token('7885a1002f5bbf605e1e5165aa56d4fcdd73325b2b94b4b863da9991')

        for date in trade_dates:
            cache_dir = rf'{self.save_dir}/{date[:4]}/{date[:6]}'
            os.makedirs(cache_dir, exist_ok=True)
            save_path = os.path.join(cache_dir, f'raw_daily_{date}.csv')

            if os.path.exists(save_path):
                print(save_path, 'has existed.')
            else:
                self.ts_download_raw_daily_bar(save_path, date)

    def ts_download_raw_daily_bar(self,save_path, date):
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

    def retry_download_check(self,tushare_path,date):
        check_raw_daily_bar_info = self.check_daily_info(tushare_path=tushare_path,date=date)
        if len(check_raw_daily_bar_info['missed_unsuspended_stock_list']):
            print(f"Missed stock list is not empty, missed stocks are {check_raw_daily_bar_info['missed_stock_list']}. Retry downloading {date}")
            os.remove(tushare_path)
            send_email_with_alert(
                subject='[Alert!!Raw Daily Bar] Unsuspended stock missed',
                content=f"Missed stock list is not empty, missed stocks are {check_raw_daily_bar_info['missed_stock_list']}. Retry downloading",
            )
            self.update_and_confirm_raw_daily_bar(today=date)
        else:
            self.notify_with_email(info_dict=check_raw_daily_bar_info)

    def notify_with_email(self, info_dict):
        subject = '[Raw Daily Bar] Data downloaded successfully'
        content = f"""
        Latest raw daily bar info is as follows:

        Download path: 
            {info_dict['tushare_path']}
        Number of TuShare stocks: 
            {info_dict['tushare_stock_count']}
        Number of RiceQuant stocks: 
            {info_dict['rice_quant_stock_count']}
        Missed stock list: 
            {info_dict['missed_stock_list']}
        NA stocks: 
            {info_dict['na_stock_list']}
        """
        send_email(subject=subject, content=content)

    def check_daily_info(self,tushare_path,date):
        tushare_df = pd.read_csv(tushare_path)
        rqdatac.init()
        ricequant_df = rqdatac.all_instruments(type='CS', market='cn', date=date)

        ricequant_df.index = ricequant_df['order_book_id'].str[:6]
        tushare_df.index = tushare_df['ts_code'].str[:6]
        tushare_missed_stock = ricequant_df.index.difference(tushare_df.index)
        tushare_missed_stock_list = ricequant_df.loc[tushare_missed_stock,'order_book_id'].tolist()

        tushare_missed_stock_s =  rqdatac.is_suspended(tushare_missed_stock_list,date,date).loc[date]
        rqdatac.reset()

        check_dict = {
            'date': date,
            'tushare_path': tushare_path,
            'tushare_stock_count': len(tushare_df),
            'rice_quant_stock_count': len(ricequant_df),
            'missed_stock_list': tushare_missed_stock_s.index.tolist(),
            'na_stock_list': tushare_df[tushare_df.isna().any(axis=1)].index.tolist(),
            'missed_unsuspended_stock_list': tushare_missed_stock_s[tushare_missed_stock_s==False].index.tolist(),
        }
        return check_dict


if __name__ == '__main__':
    RawDailyBarUpdater().update_and_confirm_raw_daily_bar(today='20230907')


