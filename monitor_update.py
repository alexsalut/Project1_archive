# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 9:03
# @Author  : Youwei Wu, Suying Zhou
# @File    : data_updater.py
# @Software: PyCharm

import time
import holidays
import datetime

from apscheduler.schedulers.blocking import BlockingScheduler

from data_updater import update_confirm_adjusted_kline
from data_updater import update_confirm_raw_daily_bar
from data_updater import update_confirm_st_list
from data_updater import update_confirm_kc50_weight


def update_schedule():
    scheduler = BlockingScheduler()
    today = time.strftime('%Y%m%d')
    # 更新时间设置为
    scheduler.add_job(execute_update,
                      'cron',
                      day_of_week="1-5",
                      hour=16, minute=41, args=[update_confirm_raw_daily_bar])
    scheduler.add_job(execute_update,
                      'cron',
                      day_of_week="1-5",
                      hour=16, minute=39, args=[update_confirm_adjusted_kline])
    scheduler.add_job(execute_update,
                      'cron',
                      day_of_week="1-5",
                      hour=10, minute=00, args=[update_confirm_kc50_weight])

    scheduler.add_job(execute_update,
                      'cron',
                      day_of_week="1-5",
                      hour=10, minute=00, args=[update_confirm_st_list])
    scheduler.start()


def execute_update(update_function):
    if not check_holiday():
        update_function()
    else:
        print('Today is holiday, no update.')


def check_holiday():
    today = datetime.datetime.today()
    return today in holidays.China()




def func_test():
    update_confirm_raw_daily_bar()
    update_confirm_adjusted_kline()
    update_confirm_st_list()
    update_confirm_kc50_weight()


if __name__ == '__main__':
    func_test()



