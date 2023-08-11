# -*- coding: utf-8 -*-
# @Time    : 2023/8/10 9:03
# @Author  : Youwei Wu, Suying Zhou
# @File    : data_updater.py
# @Software: PyCharm

import datetime

from chinese_calendar import is_workday
from apscheduler.schedulers.blocking import BlockingScheduler

from data_updater import (update_confirm_adjusted_kline,
                          update_confirm_raw_daily_bar,
                          update_confirm_st_list,
                          update_confirm_kc50_weight,
                          update_confirm_daily_turnover)


def update_schedule():
    scheduler = BlockingScheduler()

    scheduler.add_job(execute_update,
                      'cron',
                      day_of_week="1-5",
                      hour=13, minute=56, args=[update_c_data_list])

    scheduler.add_job(execute_update,
                      'cron',
                      day_of_week="1-5",
                      hour=16, minute=17, args=[update_ts_data_list])

    scheduler.add_job(execute_update,
                      'cron',
                      day_of_week="1-5",
                      hour=16, minute=30, args=[update_confirm_daily_turnover])

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
    update_confirm_st_list()
    update_confirm_kc50_weight()


def update_ts_data_list():
    update_confirm_raw_daily_bar()
    update_confirm_adjusted_kline()
