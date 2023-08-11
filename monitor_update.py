# -*- coding: utf-8 -*-
# @Time    : 2023/8/10 9:03
# @Author  : Youwei Wu, Suying Zhou
# @File    : data_updater.py
# @Software: PyCharm

import datetime
import pandas as pd

from chinese_calendar import is_workday, is_holiday
from chinese_calendar import is_in_lieu
from apscheduler.schedulers.blocking import BlockingScheduler

from data_updater import update_confirm_adjusted_kline
from data_updater import update_confirm_raw_daily_bar
from data_updater import update_confirm_st_list
from data_updater import update_confirm_kc50_weight
from data_updater import update_confirm_daily_turnover


def update_schedule():
    scheduler = BlockingScheduler()
    # 更新时间设置为
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
    if not check_trade_day():
        update_function()
    else:
        print('Today is holiday, no update.')


def check_trade_day():
    today = datetime.date.today()
    return (
            is_in_lieu(today)
            or not is_workday(today)
            or is_holiday(today)
    )


def update_c_data_list():
    update_confirm_st_list()
    update_confirm_kc50_weight()


def update_ts_data_list():
    update_confirm_raw_daily_bar()
    update_confirm_adjusted_kline()


if __name__ == '__main__':
    update_schedule()

