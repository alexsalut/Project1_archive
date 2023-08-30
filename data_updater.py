# -*- coding: utf-8 -*-
# @Time    : 2023/8/10 9:03
# @Author  : Youwei Wu, Suying Zhou
# @File    : data_updater.py
# @Software: PyCharm

import datetime

import time

import pandas as pd
from chinese_calendar import is_workday


from c_st_list_updater import ST_List_Updater
from c_kc50_weight_updater import KC50_Weight_Updater
from c_turnover_rate_updater import Turnover_Rate_Updater
from ts_kline_updater import Kline_Updater
from ts_raw_daily_bar_updater import Raw_Daily_Bar_Updater
from emc_updater import emc_updater

TUSHARE_DIR = r"\\192.168.1.116\tushare\price\daily\raw"
CHOICE_DIR = "C:/Users/Yz02/Desktop/Data/Choice"
KLINE_PATH = r"\\192.168.1.116\kline\qfq_kline_product.pkl"
ST_PATH = r'\\192.168.1.116\kline\st_list.csv'
KC50_WEIGHT_DIR = r"\\192.168.1.116\choice\reference\index_weight\sh000688\cache"


def run_update_data():
    while True:
        current_time = datetime.datetime.now()
        print(current_time)
        if is_workday(current_time) and current_time.isoweekday() < 6:
            current_minute = int(current_time.strftime('%H%M'))
            if current_minute == 1400:
                ST_List_Updater(
                    save_path=ST_PATH,
                    today=current_time.strftime('%Y%m%d'),
                    stock_default_count=0
                ).st_list_update_and_confirm()

                KC50_Weight_Updater(
                    save_dir=KC50_WEIGHT_DIR,
                    today=current_time.strftime('%Y%m%d')
                ).kc50_weight_update_and_confirm()
                time.sleep(60)

            elif current_minute == 1515:
                emc_updater()
                time.sleep(60)

            elif current_minute == 1600:
                Turnover_Rate_Updater(
                    save_dir=CHOICE_DIR,
                    today=current_time.strftime('%Y%m%d')
                ).turnover_rate_update_and_confirm()

                Raw_Daily_Bar_Updater(
                    save_dir=TUSHARE_DIR,
                ).raw_daily_bar_update_and_confirm()

                Kline_Updater(
                    raw_dir=TUSHARE_DIR,
                    save_path=KLINE_PATH,
                ).adjusted_kline_update_and_confirm()

                time.sleep(60)
            elif current_minute > 1800 or current_minute < 800:
                time.sleep(60*60)
            else:
                time.sleep(30)
        else:
            time.sleep(60*60*4)

if __name__ == '__main__':
    run_update_data()





