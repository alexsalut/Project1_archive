# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 9:03
# @Author  : Youwei Wu, Suying Zhou
# @File    : data_updater.py
# @Software: PyCharm

import os
import time
import pandas as pd

from EmQuantAPI import c

from utils import send_email, SendEmailInfo

TUSHARE_DIR = r"\\192.168.1.116\tushare\price\daily\raw"
CHOICE_DIR = "C:/Users/Yz02/Desktop/Data/Choice"
KLINE_PATH = r"\\192.168.1.116\kline\qfq_kline_product.pkl"
ST_PATH = r'\\192.168.1.116\kline\st_list.csv'
KC50_WEIGHT_DIR = r"\\192.168.1.116\choice\reference\index_weight\sh000688\cache"

class ST_List_Updater:
    def __init__(self, today=None):
        self.save_path = ST_PATH
        self.today = time.strftime('%Y%m%d') if today is None else today
        self.stock_default_count = 0

    def st_list_update_and_confirm(self):
        self.c_download_st_list()
        self.check_st_list()


    def check_st_list(self):
        data_name = 'ST_list'
        if os.path.exists(self.save_path):
            df = pd.read_csv(self.save_path, index_col=0)
            print('[ST list] file exists')
            today_stock_count = len(df[df.index == int(self.today)])
            if today_stock_count > self.stock_default_count:
                subject = rf"[{data_name}]   today file is updated"
                content = rf""""
                {self.today} st list has been accessed and the info is as follows:
                Download path:
                    {self.save_path}
                Number of st stocks today: 
                    {today_stock_count}
                """
                send_email(subject=subject, content=content, receiver=SendEmailInfo.department['research'])
                print('[ST list check] data is updated and email sent')
            else:
                print('[ST list check] today st stock data is not sufficient, retry downloading in 10 seconds')
                time.sleep(10)
                self.st_list_update_and_confirm()

    def c_download_st_list(self):
        self.c_download_index_list(
            index_ticker='001023',
        )

    def c_download_index_list(self, index_ticker):
        print(rf"Downloading {index_ticker} list until", self.today)
        print("----------------------------------")
        start_date = "20200101"
        c.start("ForceLogin=1")
        trade_dates = c.tradedates(
            startdate=start_date,
            enddate=self.today,
            options="period=1,order=1,market=CNSESH",
        ).Dates

        all_st_list = []
        for date in trade_dates:
            st_list = c.sector(index_ticker, date).Codes
            tmp_st_s = pd.Series(st_list, index=[date] * len(st_list))
            all_st_list.append(tmp_st_s)
        all_st_s = pd.concat(all_st_list)
        c.stop()

        all_st_s = all_st_s.str[-2:].str.lower() + all_st_s.str[:6]
        all_st_s.index = pd.to_datetime(all_st_s.index).strftime("%Y%m%d")
        all_st_s.to_csv(self.save_path)
        print(rf"[{index_ticker} list] updated and new .csv file generated ")




