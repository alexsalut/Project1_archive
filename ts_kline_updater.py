# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 9:03
# @Author  : Youwei Wu, Suying Zhou
# @File    : data_updater.py
# @Software: PyCharm

import os
import time
import pandas as pd

from utils import send_email
from fq_kline import FqKLine

TUSHARE_DIR = r"\\192.168.1.116\tushare\price\daily\raw"
CHOICE_DIR = "C:/Users/Yz02/Desktop/Data/Choice"
KLINE_PATH = r"\\192.168.1.116\kline\qfq_kline_product.pkl"
ST_PATH = r'\\192.168.1.116\kline\st_list.csv'
KC50_WEIGHT_DIR = r"\\192.168.1.116\choice\reference\index_weight\sh000688\cache"


class KlineUpdater:
    def __init__(self):
        self.raw_dir = TUSHARE_DIR
        self.save_path = KLINE_PATH
        self.today = time.strftime('%Y%m%d')
        self.kc_path = self.save_path.replace('.pkl', '_kc.pkl')

    def adjusted_kline_update_and_confirm(self):
        self.update_adjusted_kline()
        self.generate_email()
        self.redownload_check()

    def redownload_check(self):
        if not os.path.exists(self.kc_path) or os.path.getsize(self.kc_path) <= 80000:
            print(f'{self.kc_path} does not exist or no sufficient data.')
            time.sleep(300)
            self.adjusted_kline_update_and_confirm()

    def generate_email(self):
        if os.path.exists(self.kc_path):
            subject = '[Adjusted Kline] Data finish processing'
            adjusted_kline = pd.read_pickle(self.kc_path)
            print(f'{self.kc_path} exists.')
            adjusted_kline.query('ticker=="sh688086"')
            info_dict = self.data_check(adjusted_kline)
            content = f"""
            Today's adjusted kline has been generated.
            File path:
                {self.kc_path}
            Number of KC stocks today:
                 {info_dict['Total Number of Stocks']}
            NaN: 
                {info_dict['NaN']}
            Negative: 
                {info_dict['Negative']}
            Zero: 
                {info_dict['Zero']}
            Open&Close out of High&Low: 
                {info_dict['Open&Close out of High&Low']}
            Extreme High&Low Difference(>30%): 
                {info_dict['Extreme High&Low Difference']}
            Extreme Daily Ret(>20.05%): 
                {info_dict['Extreme Daily Ret']}
            """
        else:
            subject = '[Adjusted Kline] File is non-existent. Retry downloading in 5 minutes.'
            content = None
        send_email(subject, content)

    def data_check(self, adjusted_kline):
        keys = [
            'Total Number of Stocks',
            'NaN',
            'Negative',
            'Zero',
            'Open&Close out of High&Low',
            'Extreme High&Low Difference',
            'Extreme Daily Ret',
        ]
        info_dict = {key: self.df_check(adjusted_kline, option=key) for key in keys}
        return info_dict

    def df_check(self, adjusted_kline, option):
        print(option)
        if option == 'NaN':
            return adjusted_kline[adjusted_kline.isna()].dropna(how='all').index.tolist()
        elif option == 'Total Number of Stocks':
            return len(adjusted_kline.loc[self.today])
        elif option == 'Negative':
            return adjusted_kline[(adjusted_kline<0)].iloc[:,[0,1,2,3,4,5,-1]].dropna(how='all').index.tolist()
        elif option == 'Zero':
            df = (adjusted_kline.loc[:,:'amount']==0)
            return df[df].dropna().index.tolist()
        elif option == 'Open&Close out of High&Low':
            return adjusted_kline[(adjusted_kline['close'] > adjusted_kline['high'])|
                                  (adjusted_kline['open'] > adjusted_kline['high'])|
                                  (adjusted_kline['close'] < adjusted_kline['low']) |
                                  (adjusted_kline['open'] < adjusted_kline['low'])].dropna(how='all').index.tolist()
        elif option == 'Extreme High&Low Difference':
            return adjusted_kline[(adjusted_kline['high'] - adjusted_kline['low'])/adjusted_kline['low'] > 0.3].dropna(how='all').index.tolist()
        elif option == 'Extreme Daily Ret':
            return adjusted_kline.query('abs(pct_chg)>0.2005')['pct_chg'].apply(lambda x: f'{x:.2%}')
        else:
            raise ValueError('Option not available')

    def update_adjusted_kline(self):
        FqKLine(
            tushare_dir=self.raw_dir,
            save_path=self.save_path,
        ).gen_qfq_kline()

if __name__ == '__main__':
    KlineUpdater().generate_email()
