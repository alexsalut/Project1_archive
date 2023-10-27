# -*- coding: utf-8 -*-
# @Time    : 2023/8/10 9:03
# @Author  : Youwei Wu, Suying Zhou
# @File    : data_updater.py
# @Software: PyCharm

import time

import rqdatac as rq

from choice.c_st_list_updater import ST_List_Updater
from choice.c_kc50_weight_updater import KC50WeightUpdater
# from choice.c_turnover_rate_updater import TurnoverRateUpdater
from choice.kc50_composition import download_check_kc50_composition

from t.ts_kline_updater import KlineUpdater
from t.ts_raw_daily_bar_updater import RawDailyBarUpdater

from position.position_check import check_notify_position

from record.account_recorder import account_recorder
from monitor.cnn_daily_record import CnnDailyRecord

from rice_quant.risk_exposure import gen_expo_df
from rice_quant.live_kline_updater import gen_ricequant_virtual_kline, gen_stock_list
from performance_analysis.analysis import daily_performance_eval

from web_data.index_futures import update_daily_futures
from util.trading_calendar import TradingCalendar as TC
from util.utils import SendEmailInfo
from util.send_email import Mail, R
from tick_check.tick_check import CheckTick
from account_check.account_cross_check import AccountCheck


def auto_update():
    try:
        while True:
            today = time.strftime('%Y%m%d')  # 每次循环重新记录下
            if today in TC.trading_calendar:
                print(time.strftime('%X'))
                run_daily_update()
            else:
                print(time.strftime('%X'), f'Today {today} is not trading day, sleep 12 hours.')
                time.sleep(12 * 60 * 60)
    except Exception as e:
        print(e)
        Mail().send(
            subject=f'daily updater报错，1分钟后重试',
            body_content=f'{e}',
            receivers=R.department['research'][0],
        )
        time.sleep(60)
        auto_update()


def run_daily_update():
    current_minute = int(time.strftime('%H%M'))
    if current_minute == 830:
        AccountCheck().notify_check_with_email()
        account_recorder(adjust=True)

    elif current_minute == 1400:
        ST_List_Updater().st_list_update_and_confirm()
        download_check_kc50_composition()

    elif current_minute in [1429, 1444]:
        gen_quick_virtual_kline(current_minute)

    elif current_minute in [1453, 1501]:
        receivers = SendEmailInfo.department['research'] + SendEmailInfo.department['tech']
        check_notify_position(receivers)

    elif current_minute == 1510:
        CnnDailyRecord().update_monitor()

    elif current_minute == 1516:
        account_recorder()

    elif current_minute == 1630:
        update_after_close()

    elif current_minute == 1745:
        gen_expo_df(time.strftime('%Y%m%d'))

    elif current_minute > 1800:
        print(time.strftime('%X'), f"Today's task has finished, sleep 12 hours.")
        time.sleep(12 * 60 * 60)

    time.sleep(60)


def gen_quick_virtual_kline(current_minute):
    date = time.strftime('%Y%m%d')
    stock_list = gen_stock_list(date)

    while int(time.strftime('%H%M')) == current_minute:
        print(time.strftime('%X'), 'Wait for update!')
        time.sleep(0.1)
    gen_ricequant_virtual_kline(stock_list, date)


def update_after_close():
    KC50WeightUpdater().kc50_weight_update_and_confirm()
    # TurnoverRateUpdater().turnover_rate_update_and_confirm()
    RawDailyBarUpdater().update_and_confirm_raw_daily_bar()
    KlineUpdater().update_confirm_adjusted_kline()
    update_daily_futures()
    daily_performance_eval()
    CheckTick().multi_task_daily_check()


if __name__ == '__main__':
    auto_update()
