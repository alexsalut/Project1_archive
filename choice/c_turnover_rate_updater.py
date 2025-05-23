# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 9:03
# @Author  : Youwei Wu, Suying Zhou
# @File    : product_update.py
# @Software: PyCharm

import os
import time
import pandas as pd

from EmQuantAPI import c

from util.send_email import Mail, R
from util.utils import transfer_to_jy_ticker
from util.file_location import FileLocation as FL


class TurnoverRateUpdater:
    def __init__(self, today=None):
        self.save_dir = FL.turnover_dir
        self.today = time.strftime('%Y%m%d') if today is None else today

    def turnover_rate_update_and_confirm(self):
        self.c_download_turnover_rate_history()
        save_path = rf'{self.save_dir}/daily_turnover_rate/{self.today[:4]}/{self.today[:6]}/{self.today}.csv'
        self.check_turnover_rate(save_path=save_path)

    def check_turnover_rate(self, save_path):
        if not os.path.exists(save_path):
            self.redownload_turnover_rate(save_path=save_path)
        else:
            error_list, turnover_info_dict = self.get_turnover_info(save_path=save_path)
            if len(error_list) == 0:
                self.send_turnover_email(save_path=save_path, turnover_info_dict=turnover_info_dict)
            else:
                subject = '[Alert!!! Turnover Rate] data with alert.'
                content = f"""
                <table width="800" border="0" cellspacing="0" cellpadding="4">
                <tr>
                <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>Error list</b></td>
                </tr>
                <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
                {error_list}
                """
                Mail().send(subject=subject, body_content=content, receivers=R.department['research'])
                self.redownload_turnover_rate(save_path=save_path)

    @staticmethod
    def get_turnover_info(save_path):
        error_list = []
        turnover_rate_df = pd.read_csv(save_path, index_col=0)
        s = turnover_rate_df[(turnover_rate_df > 100) | (turnover_rate_df < 0)].any(axis=1)
        turnover_info_dict = {
            'stock count': len(turnover_rate_df.index),
            'na list': turnover_rate_df[turnover_rate_df.isna().any(axis=1)].index.tolist(),
            'anomaly list': s[s].index.tolist(),
        }
        if turnover_info_dict['stock count'] == 0:
            error_list.append(f'[Turnover Rate] No stock in the file {save_path}.')
        if len(turnover_info_dict['anomaly list']) > 0:
            error_list.append('[Turnover Rate] File contains anomalous data which >100 or <0.')
        if len(turnover_info_dict['na list']) > 3:
            error_list.append('[Turnover Rate] more than 3 stocks has missing data.')
        return error_list, turnover_info_dict

    def redownload_turnover_rate(self, save_path):
        if os.path.exists(save_path):
            os.remove(save_path)
            print(f'[Turnover Rate]{save_path} Redownloading in 10 seconds')
        time.sleep(10)
        self.turnover_rate_update_and_confirm()

    @staticmethod
    def send_turnover_email(save_path, turnover_info_dict):
        subject = '[Turnover Rate] File downloaded successfully.'
        content = f"""
        <table width="800" border="0" cellspacing="0" cellpadding="4">
        <tr>
        <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>Turnover Rate Overview</b></td>
        </tr>
        <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
        <p>Today's turnover rate info is as follows if any:</p>
        <p>Download path:</p>
            {save_path}
        <p>Number of stocks included:</p>            
            {turnover_info_dict['stock count']}  
        <p>Details(Code) of stocks with missing values:</p>
            {turnover_info_dict['na list']}
        """
        Mail().send(subject=subject, body_content=content, receivers=R.department['research'])

    def c_download_turnover_rate_history(self):
        print(f"Downloading historical turnover rate until {self.today}")
        print("-------------------------------------------------")

        c.start("ForceLogin=1")
        trade_dates = c.tradedates(
            "2022-06-30",
            self.today,
            "period=1,order=1,market=CNSESH",
        ).Dates
        c.stop()

        date_list = pd.to_datetime(trade_dates).strftime("%Y%m%d").tolist()

        for date in date_list:
            cache_dir = rf'{self.save_dir}/daily_turnover_rate/{date[:4]}/{date[:6]}'
            os.makedirs(cache_dir, exist_ok=True)
            save_path = os.path.join(cache_dir, f'{date}.csv')
            if os.path.exists(save_path):
                print(f'[Turnover rate] {date} csv file has existed.')
            else:
                self.c_download_daily_turnover_rate(index_ticker='001071', date=date, save_path=save_path)

    @staticmethod
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
        print(f"[Turnover Rate] {date} updated and new .csv file generated ")
