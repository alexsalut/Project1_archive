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
KLINE_PATH = r"\\192.168.1.116\kline\qfq_kline_product_kc.pkl"
ST_PATH = r'\\192.168.1.116\kline\st_list.csv'
KC50_WEIGHT_DIR = r"\\192.168.1.116\choice\reference\index_weight\sh000688\cache"

class Kline_Updater:
    def __init__(self, raw_dir, save_path):
        self.raw_dir = raw_dir
        self.save_path = save_path
        self.today = time.strftime('%Y%m%d')

    def adjusted_kline_update_and_confirm(self):
        self.update_adjusted_kline()
        self.generate_email()
        self.redownload_check()


    def redownload_check(self):
        if not os.path.exists(self.save_path) or os.path.getsize(self.save_path) <= 5500000:
            print(f'{self.save_path} does not exist or no sufficient data.')
            time.sleep(300)
            self.adjusted_kline_update_and_confirm()



    def generate_email(self):
        if os.path.exists(self.save_path):
            subject = '[Adjusted Kline] Data finish processing'
            adjusted_kline = pd.read_pickle(self.save_path)
            print(f'{self.save_path} exists.')
            info_dict = self.data_check(adjusted_kline)
            content = f"""
            Today's adjusted kline has been generated.
            Number of stocks for today is {info_dict['Total_Number of Stocks']}\n
            NaN: 
            {info_dict['NaN']}\n
            Negative: 
            {info_dict['Negative']}\n
            Zero: 
            {info_dict['Zero']}\n
            Open&Close out of High&Low: 
            {info_dict['Open&Close out of High&Low']}\n
            Extreme High&Low Difference: 
            {info_dict['Extreme High&Low Difference']}\n
            Extreme Daily Ret: 
            {info_dict['Extreme Daily Ret']}\n
            """
        else:
            subject = '[Adjusted Kline] File is non-existent. Retry downloading in 5 minutes.'
            content = None
        send_email(subject, content)

    def data_check(self, adjusted_kline):
        keys = [
            'Total_Number of Stocks',
            'NaN',
            'Negative',
            'Zero',
            'Open&Close out of High&Low',
            'Extreme High&Low Difference',
            'Extreme Daily Ret']
        dict = {key: None for key in keys}

        for key in dict.keys():
            if key == 'Total_Number of Stocks':
                dict[key] = len(adjusted_kline[adjusted_kline.index.get_level_values(0) == self.today])
            else:
                dict[key] = adjusted_kline.apply(lambda row: self.row_check(row, option=key), axis=1).dropna()
        return dict

    def row_check(self, row, option='NaN'):
        if option == 'NaN':
            list = row[row.isna()].index.tolist()
            return list if len(list) > 0 else None
        elif option == 'Negative':
            list = row[row < 0].index.tolist()
            list = list.drop('pct_chg') if 'pct_chg' in list else list
            return list if len(list) > 0 else None
        elif option == 'Zero':
            list = row[row == 0].index.tolist()
            return list if len(list) > 0 else None
        elif option == 'Open&Close out of High&Low':
            if (min(row['open'], row['close']) > row['low']) | (max(row['open'], row['close']) < row['high']):
                return row.name
            else:
                return None
        elif option == 'Extreme High&Low Difference':
            return row.name if (row['high'] - row['low'])/row['low'] > 0.3 else None
        elif option == 'Extreme Daily Ret':
            return row.name if abs(row['pct_chg']) > 0.2 else None
        else:
            raise ValueError('Option not available')






    def update_adjusted_kline(self):
        FqKLine(
            tushare_dir=self.raw_dir,
            save_path=self.save_path,
        ).gen_qfq_kline()

if __name__ == '__main__':
    adjusted_kline = pd.read_pickle(KLINE_PATH)
    adjusted_kline['id'] = None
    Kline_Updater(
        raw_dir=TUSHARE_DIR,
        save_path=KLINE_PATH,
    ).adjusted_kline_update_and_confirm()

