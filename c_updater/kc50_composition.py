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


def download_check_kc50_composition(date=None):
    date = time.strftime('%Y%m%d') if date is None else date
    c_download_kc50_composition(date)
    save_path = rf'\\192.168.1.116\choice\reference\sh000688\{date}.csv'
    kc50_composition = pd.read_csv(save_path)
    if len(kc50_composition) == 50:
        print('[kc50 composition] no error found, downloaded successfully')
        subject = f'[kc50 composition] downloaded successfully'
        content = f"""
        Download path:
        {save_path}
        """
        send_email(subject=subject, content=content, receiver=SendEmailInfo.department['research'])
    else:
        print('[kc50 composition] Stock number not correct, retry downloading in five mins')
        send_email(subject='[Alert! kc 50 composition not correct]', receiver=SendEmailInfo.department['research'][0])
        time.sleep(300)
        download_check_kc50_composition(date)


def c_download_kc50_composition(date):
    c.start("ForceLogin=1")
    df = c.sector("009007673", date, options='ispandas=1')['SECUCODE']
    c.stop()
    save_path = rf'\\192.168.1.116\choice\reference\sh000688\{date}.csv'
    df.to_csv(save_path, index=False)
    print(f'[kc50 composition] {date} file has downloaded.')


if __name__ == '__main__':
    c_download_kc50_composition(date='20230919')
