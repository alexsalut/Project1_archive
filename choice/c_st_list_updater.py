# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 9:03
# @Author  : Youwei Wu, Suying Zhou
# @File    : product_update.py
# @Software: PyCharm

import os
import time
import pandas as pd

from EmQuantAPI import c
from util.file_location import FileLocation as FL
from util.send_email import Mail, R


class ST_List_Updater:
    def __init__(self, today=None, year='2024'):
        self.today = time.strftime('%Y%m%d') if today is None else today
        self.year = year
        self.save_path = rf'D:\data\st_list\st_list{year}.pkl'
        self.stock_default_count = 0

    def st_list_update_and_confirm(self):
        self.c_download_st_list()
        self.check_st_list()

    def check_st_list(self):
        data_name = 'ST_list'
        if os.path.exists(self.save_path):
            df = pd.read_pickle(self.save_path)
            print('[ST list] file exists')
            today_stock_count = len(df[df.index == self.today])
            if today_stock_count > self.stock_default_count:
                subject = rf"[{data_name}]   today file is updated"
                content = rf"""
                <table width="800" border="0" cellspacing="0" cellpadding="4">
                <tr>
                <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>ST list更新完成</b></td>
                </tr>
                <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
                <p>{self.today} st list has been accessed and the info is as follows:</p>
                <p><b>Download path:</b></p>
                {self.save_path}
                <p><b>Number of st stocks today:</b></p> 
                {today_stock_count}
                """
                Mail().send(subject=subject, body_content=content, receivers=R.staff['zhou'])
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
        start_date = f"{self.year}0101"
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

        all_st_s.index = pd.to_datetime(all_st_s.index).strftime("%Y%m%d")
        all_st_s.to_pickle(self.save_path)
        print(rf"[{index_ticker} list] updated and new .pkl file generated ")

if __name__ == '__main__':
    ST_List_Updater().st_list_update_and_confirm()