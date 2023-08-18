# -*- coding: utf-8 -*-
# @Time    : 2023/8/10 9:03
# @Author  : Youwei Wu, Suying Zhou
# @File    : data_updater.py
# @Software: PyCharm

import datetime

import pandas as pd
from chinese_calendar import is_workday
from apscheduler.schedulers.background import BlockingScheduler

from c_st_list_updater import st_list_update_and_confirm
from c_kc50_weight_updater import kc50_weight_update_and_confirm
from c_turnover_rate_updater import turnover_rate_update_and_confirm
from ts_kline_updater import adjusted_kline_update_and_confirm
from ts_raw_daily_bar_updater import raw_daily_bar_update_and_confirm


def update_schedule():
    job_defaults = {
        'coalesce': True,
        'misfire_grace_time': None,
        'max_instances': 1
    }
    # scheduler = BackgroundScheduler(job_defaults=job_defaults)
    scheduler = BlockingScheduler(job_defaults=job_defaults)
    scheduler.add_job(
        execute_update,
        'cron',
        day_of_week="1-5",
        hour=13, minute=47, args=[update_c_data_list],
    )  # 13:47

    scheduler.add_job(
        execute_update,
        'cron',
        day_of_week="1-5",
        hour=16, minute=17, args=[update_ts_data_list],
    )   # 16:17

    scheduler.add_job(
        execute_update,
        'cron',
        day_of_week="1-5",
        hour=16, minute=30, args=[turnover_rate_update_and_confirm],
    )   # 16:30

    scheduler.add_job(time_update, 'interval', minutes=10)
    scheduler.start()


def time_update():
    now = datetime.datetime.now()
    print('Time:', now)


def execute_update(update_function):
    today = datetime.datetime.now()
    if is_workday(today) and today.isoweekday() < 6:
        update_function()
    else:
        print('Today is holiday, no update.')


def update_c_data_list():
    st_list_update_and_confirm()
    kc50_weight_update_and_confirm()


def update_ts_data_list():
    raw_daily_bar_update_and_confirm()
    adjusted_kline_update_and_confirm()

if __name__ == '__main__':
    update_schedule()




