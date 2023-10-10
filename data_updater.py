# -*- coding: utf-8 -*-
# @Time    : 2023/8/10 9:03
# @Author  : Youwei Wu, Suying Zhou
# @File    : data_updater.py
# @Software: PyCharm

import time

from c_updater.c_st_list_updater import ST_List_Updater
from c_updater.c_kc50_weight_updater import KC50WeightUpdater
# from c_updater.c_turnover_rate_updater import TurnoverRateUpdater
from c_updater.kc50_composition import download_check_kc50_composition

from tushare_updater.ts_kline_updater import KlineUpdater
from tushare_updater.ts_raw_daily_bar_updater import RawDailyBarUpdater

from account_position.position_check import check_notify_position

from account_record.account_recorder import account_recorder
from daily_cnn_record.cnn_daily_record import CnnDailyRecord

from rice_quant_updater.risk_exposure import gen_expo_df
from rice_quant_updater.live_kline_updater import gen_ricequant_virtual_kline

from web_data_updater.index_futures import update_daily_futures
from util.trading_calendar import TradingCalendar as TC
from monitor.account_monitor import account_monitor


def auto_update():
    while True:
        today = time.strftime('%Y%m%d')  # 每次循环重新记录下
        if today in TC.trading_calendar:
            print(time.strftime('%X'))
            run_daily_update()
        else:
            print(time.strftime('%X'), f'Today {today} is not trading day, sleep 12 hours.')
            time.sleep(12 * 60 * 60)


def run_daily_update():
    current_minute = int(time.strftime('%H%M'))
    if current_minute == 1400:
        ST_List_Updater().st_list_update_and_confirm()
        download_check_kc50_composition()

    elif current_minute in [1429, 1444]:
        gen_quick_virtual_kline(current_minute)

    elif current_minute in [1452, 1500]:
        check_notify_position()

    elif current_minute == 1520:
        CnnDailyRecord().update_monitor()
        account_recorder()

    elif current_minute == 1630:
        update_after_close()

    elif current_minute > 1800:
        print(time.strftime('%X'), f"Today's task has finished, sleep 12 hours.")
        time.sleep(12 * 60 * 60)

    time.sleep(60)


def gen_quick_virtual_kline(current_minute):
    while int(time.strftime('%H%M')) == current_minute:
        print(time.strftime('%X'), 'Wait for update!')
        time.sleep(0.5)
    gen_ricequant_virtual_kline()


def update_after_close():
    KC50WeightUpdater().kc50_weight_update_and_confirm()
    # TurnoverRateUpdater().turnover_rate_update_and_confirm()
    RawDailyBarUpdater().update_and_confirm_raw_daily_bar()
    KlineUpdater().update_confirm_adjusted_kline()
    update_daily_futures()
    gen_expo_df(time.strftime('%Y%m%d'))


if __name__ == '__main__':
    # auto_update()
    gen_quick_virtual_kline(1353)
