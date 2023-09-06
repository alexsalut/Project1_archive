# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 9:03
# @Author  : Youwei Wu, Suying Zhou
# @File    : data_updater.py
# @Software: PyCharm

import os
import time
import pandas as pd


from EmQuantAPI import c

from utils import transfer_to_jy_ticker, send_email


TUSHARE_DIR = r"\\192.168.1.116\tushare\price\daily\raw"
CHOICE_DIR = "C:/Users/Yz02/Desktop/Data/Choice"
KLINE_PATH = r"\\192.168.1.116\kline\qfq_kline_product.pkl"
ST_PATH = r'\\192.168.1.116\kline\st_list.csv'
KC50_WEIGHT_DIR = r"\\192.168.1.116\choice\reference\index_weight\sh000688\cache"

class KC50_Weight_Updater:
    def __init__(self, save_dir, today):
        self.save_dir = save_dir
        self.today = time.strftime('%Y%m%d') if today is None else today

    def kc50_weight_update_and_confirm(self):
        save_path = os.path.join(self.save_dir, f'{self.today}.pkl')
        self.c_download_kc50_weight(self.today, save_path)
        subject, content = self.kc50_weight_email_content(save_path=save_path)
        send_email(subject=subject, content=content)

    def kc50_weight_email_content(self, save_path):
        data_name = 'kc50_weight'
        alert = []
        if os.path.exists(save_path):
            df = pd.read_pickle(save_path)
            print(f'{data_name} file exists')
            subject, alert = self.kc50_weight_check(df)
        else:
            subject = rf'[{data_name}] has not downloaded yet'
        content = f"""
        {data_name} update on {self.today}.
        Download path: {save_path}
        Data alert check if any: {alert}
        """
        return subject, content

    def kc50_weight_check(self,df):
        alert = []
        data_name = 'KC50_weight'
        if df.empty:
            subject = rf"[{data_name}]  No data on the downloaded file"
        else:
            if abs(df.WEIGHT.sum()-1) > 0.00001:
                alert.append('Sum of weight is not 1')
            if df.shape[0] != 50:
                alert.append('Number of stocks is not 50')
            if not all(value > 0 for value in df.WEIGHT):
                alert.append('Weight has negative value')
            if len(alert) == 0:
                subject = rf"[{data_name}] has successfully downloaded"
            else:
                subject = rf"[{data_name}] has successfully downloaded with alert"
        return subject, alert


    def download_history_kc50_weight(self, start_date, end_date):
        c.start()
        trade_dates = c.tradedates(
            startdate=start_date,
            enddate=end_date,
            options="period=1,order=1,market=CNSESH",
        ).Dates


    def c_download_kc50_weight(self, date, save_path):
        os.makedirs(self.save_dir, exist_ok=True)
        self.c_download_index_weight(
            index_ticker='000688.SH',
            date=date,
            save_path=save_path
        )

    def c_download_index_weight(self, index_ticker, date, save_path):
        print("Downloading Index Composition Weight")
        print("-----------------------------------")
        jy_ticker = transfer_to_jy_ticker([index_ticker])[0]

        c.start("ForceLogin=1")
        df = c.ctr(
            "INDEXCOMPOSITION",
            "SECUCODE,WEIGHT",
            f"IndexCode={index_ticker},EndDate={date},ispandas=1",
        )
        c.stop()

        df.to_pickle(save_path)
        print(f'{save_path}', 'has downloaded.')




if __name__ == '__main__':
    kc50_weight_updater = KC50_Weight_Updater(save_dir=KC50_WEIGHT_DIR, today=None)

    kc50_weight_updater.c_download_kc50_weight(date='20210709', save_path=rf'{KC50_WEIGHT_DIR}/20210709.pkl')




