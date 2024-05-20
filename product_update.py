# -*- coding: utf-8 -*-
# @Time    : 2023/8/10 9:03
# @Author  : Youwei Wu, Suying Zhou
# @File    : product_update.py
# @Software: PyCharm

import time

import pandas as pd

from tushare.ts_kline_updater import KlineUpdater
from tushare.ts_raw_daily_bar_updater import RawdailyBarUpdater
from util.trading_calendar import TradingCalendar
from regular_update.get_citic_rq import get_citic_rq
from regular_update.download_cap import download_cap
from regular_update.download_rq_rzrq import download_rzrq_file, check_rzrq_limit_file
from rice_quant.conv_raw_daily_bar import download_conv_raw_daily_bar
from prepare_arbitrage_daily_data.concat_all_data import concat_all_data

def product_update():
    while True:
        today = time.strftime('%Y%m%d')  # 每次循环重新记录下
        if today in TradingCalendar.trading_calendar:
            run_daily_update()
        else:
            print(time.strftime('%X'),
                  f'Today {today} is not trading day, sleep 6 hours.')
            time.sleep(6 * 60 * 60)


def run_daily_update():
    current_minute = int(time.strftime('%H%M'))
    if current_minute == 850:
        download_rzrq_file()
        get_citic_rq()

    elif current_minute == 910:
        concat_all_data()

    elif current_minute == 1300:
        check_rzrq_limit_file()

    elif current_minute == 1630:
        download_cap()
        RawdailyBarUpdater().update_and_confirm_raw_daily_bar()
        KlineUpdater().update_confirm_adjusted_kline()
        download_conv_raw_daily_bar()


    elif current_minute % 5 == 0:
        print(time.strftime('%x %X'))

    time.sleep(60)


if __name__ == '__main__':
    product_update()
