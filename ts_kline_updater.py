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


def adjusted_kline_update_and_confirm():
    update_adjusted_kline()
    subject, content = adjusted_kline_email_content(save_path=KLINE_PATH)
    send_email(subject, content)


def adjusted_kline_email_content(save_path):
    today = time.strftime('%Y%m%d')
    if os.path.exists(save_path):
        adjusted_kline = pd.read_pickle(save_path)
        subject, stock_count, na_stock = adjusted_kline_check(adjusted_kline, today)
    else:
        subject = '[adjusted_kline] file is non-existent'
        stock_count = None
        na_stock = None
        save_path = None
    content = f"""
        Today's raw daily bar info is as follows if any:
    Download path:
    {save_path}
    Number of stocks included:            {stock_count}  
    Details(Code) of stocks with missing values:
    {na_stock}
    """
    return subject, content


def adjusted_kline_check(adjusted_kline, today):
    if adjusted_kline.dropna(how='all').empty:
        subject = '[adjusted_kline] file is empty'
        stock_count = 0
        na_stock = []
    else:
        today_kline = adjusted_kline[adjusted_kline.index.get_level_values(0) == today]
        stock_count = len(today_kline)
        na_stock = today_kline[today_kline.isna().any(axis=1)].index.tolist()
        if stock_count < 5000:
            subject = '[adjusted_kline] Data downloaded with alert.'
        else:
            subject = '[adjusted_kline] Data downloaded successfully.'
    return subject, stock_count, na_stock


def update_adjusted_kline():
    FqKLine(
        tushare_dir=TUSHARE_DIR,
        save_path=KLINE_PATH,
    ).gen_qfq_kline()


