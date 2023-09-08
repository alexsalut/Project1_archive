# -*- coding: utf-8 -*-
# @Time    : 2023/8/10 9:03
# @Author  : Youwei Wu, Suying Zhou
# @File    : data_updater.py
# @Software: PyCharm

import datetime
import time

from chinese_calendar import is_workday

from c_st_list_updater import ST_List_Updater
from c_kc50_weight_updater import KC50WeightUpdater
from c_turnover_rate_updater import TurnoverRateUpdater
from ts_kline_updater import KlineUpdater
from ts_raw_daily_bar_updater import RawDailyBarUpdater
from emc_updater_v0 import emc_updater
from account_updater import Account
from monitorupdater import MonitorUpdater

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
                ST_List_Updater().st_list_update_and_confirm()
                KC50WeightUpdater().kc50_weight_update_and_confirm()
                time.sleep(60)

            # elif current_minute == 1502:
            #     MonitorUpdater().update_monitor()
            #     Account().account_update()
            #     time.sleep(60)

            # elif current_minute == 1515:
            #     emc_updater()
            #     time.sleep(60)

            elif current_minute == 1600:
                TurnoverRateUpdater().turnover_rate_update_and_confirm()
                RawDailyBarUpdater().update_and_confirm_raw_daily_bar()
                KlineUpdater().adjusted_kline_update_and_confirm()
                time.sleep(60)
            elif current_minute > 1800 or current_minute < 800:
                time.sleep(60*60)
            else:
                time.sleep(30)
        else:
            time.sleep(60*60*4)


if __name__ == '__main__':
    run_update_data()
