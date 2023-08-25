# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 9:03
# @Author  : Youwei Wu, Suying Zhou
# @File    : data_updater.py
# @Software: PyCharm

import os
import time
import pandas as pd

from EmQuantAPI import c

from utils import send_email

TUSHARE_DIR = r"\\192.168.1.116\tushare\price\daily\raw"
CHOICE_DIR = "C:/Users/Yz02/Desktop/Data/Choice"
KLINE_PATH = r"\\192.168.1.116\kline\qfq_kline_product.pkl"
ST_PATH = r'\\192.168.1.116\kline\st_list.csv'
KC50_WEIGHT_DIR = r"\\192.168.1.116\choice\reference\index_weight\sh000688\cache"


def st_list_update_and_confirm(today=None):
    save_path = ST_PATH
    today = time.strftime('%Y%m%d') if today is None else today
    c_download_st_list(today)
    subject, content = st_list_email_content(today, save_path=save_path, stock_default_count=0)
    send_email(subject=subject, content=content)


def st_list_email_content(today, save_path, stock_default_count=0):
    data_name = 'st_list'
    if os.path.exists(save_path):
        df = pd.read_csv(save_path, index_col=0)
        print(f'{data_name} file exists')
        stock_count = len(df[df.index == int(today)])
        if df.empty:
            subject = f"No data on the downloaded {data_name} file"
        elif stock_count > stock_default_count:
            subject = rf"[{data_name}]   today file is updated"
        else:
            subject = rf"[{data_name}]   today file is updated with alert"
        content = rf""""
        {today} {data_name} has been accessed and the info is as follows:
        Download path:
        {save_path}
        Number of stocks included today: {stock_count}

        """
    else:
        subject = f"{data_name} file does not exist"
        content = f""""
        {today} {data_name} has not been accessed successfully
        """
    return subject, content


def c_download_st_list(today=None):
    today = time.strftime('%Y%m%d') if today is None else today
    c_download_index_list(
        index_ticker='001023',
        date=today,
        save_path=ST_PATH,
    )


def c_download_index_list(index_ticker, date, save_path):
    print(rf"Downloading {index_ticker} list until", date)
    print("----------------------------------")
    start_date = "20200831"
    c.start("ForceLogin=1")
    trade_dates = c.tradedates(
        startdate=start_date,
        enddate=date,
        options="period=1,order=1,market=CNSESH",
    ).Dates
    # # 2023-08-25 14:49:55
    # data = c.tradedates("2020-08-30", "2023-08-25", "period=1,order=1,market=CNSESH")


    all_st_list = []
    for date in trade_dates:
        st_list = c.sector(index_ticker, date).Codes
        tmp_st_s = pd.Series(st_list, index=[date] * len(st_list))
        all_st_list.append(tmp_st_s)
    all_st_s = pd.concat(all_st_list)
    c.stop()

    all_st_s = all_st_s.str[-2:].str.lower() + all_st_s.str[:6]
    all_st_s.index = pd.to_datetime(all_st_s.index).strftime("%Y%m%d")
    all_st_s.to_csv(save_path)
    print(rf"{index_ticker} list updated and new .csv file generated ")


if __name__ == '__main__':
    c_download_st_list()

