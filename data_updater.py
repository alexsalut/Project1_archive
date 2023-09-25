# -*- coding: utf-8 -*-
# @Time    : 2023/8/10 9:03
# @Author  : Youwei Wu, Suying Zhou
# @File    : data_updater.py
# @Software: PyCharm

import datetime
import time
import multiprocessing

from c_updater.c_st_list_updater import ST_List_Updater
from c_updater.c_kc50_weight_updater import KC50WeightUpdater
from c_updater.c_turnover_rate_updater import TurnoverRateUpdater
from c_updater.kc50_composition import download_check_kc50_composition

from tushare_updater.ts_kline_updater import KlineUpdater
from tushare_updater.ts_raw_daily_bar_updater import RawDailyBarUpdater

from account_position.position_check import check_notify_position

from account_record.account_recorder import account_recorder
from daily_cnn_record.cnn_daily_record import CnnDailyRecord

from rice_quant_updater.risk_exposure import gen_expo_df

from web_data_updater.index_futures import update_daily_futures
from util.trading_calendar import TradingCalendar as TC


def run_daily_update():
    while True:
        current_time = datetime.datetime.now()
        print(current_time)
        if TC().check_is_trading_day(current_time.strftime('%Y%m%d')):
            current_minute = int(current_time.strftime('%H%M'))
            if current_minute == 1400:
                ST_List_Updater().st_list_update_and_confirm()
                download_check_kc50_composition()
                time.sleep(60)

            elif current_minute == 1452:
                check_notify_position()
                time.sleep(60)

            elif current_minute == 1505:
                check_notify_position()
                CnnDailyRecord().update_monitor()
                time.sleep(60)

            elif current_minute == 1520:
                account_recorder()
                time.sleep(60)

            elif current_minute == 1630:
                KC50WeightUpdater().kc50_weight_update_and_confirm()
                TurnoverRateUpdater().turnover_rate_update_and_confirm()
                RawDailyBarUpdater().update_and_confirm_raw_daily_bar()
                KlineUpdater().update_confirm_adjusted_kline()
                update_daily_futures()
                time.sleep(60)

            elif current_minute == 1830:
                gen_expo_df(time.strftime('%Y%m%d'))
                time.sleep(60)
            elif current_minute > 1900 or current_minute < 800:
                time.sleep(60 * 60)
            else:
                time.sleep(30)
        else:
            time.sleep(60 * 60 * 4)


if __name__ == '__main__':
    run_daily_update()
