# -*- coding: utf-8 -*-
# @Time    : 2023/8/10 9:03
# @Author  : Youwei Wu, Suying Zhou
# @File    : data_updater.py
# @Software: PyCharm

import datetime

import time
from chinese_calendar import is_workday


from c_st_list_updater import st_list_update_and_confirm
from c_kc50_weight_updater import kc50_weight_update_and_confirm
from c_turnover_rate_updater import turnover_rate_update_and_confirm
from ts_kline_updater import adjusted_kline_update_and_confirm
from ts_raw_daily_bar_updater import raw_daily_bar_update_and_confirm


def run_update_data():
    while True:
        current_time = datetime.datetime.now()
        print(current_time)
        if is_workday(current_time) and current_time.isoweekday() < 6:
            current_minute = int(current_time.strftime('%H%M'))
            if current_minute == 1347:
                st_list_update_and_confirm()
                kc50_weight_update_and_confirm()
                time.sleep(60)
            elif current_minute == 1617:
                raw_daily_bar_update_and_confirm()
                adjusted_kline_update_and_confirm()
                turnover_rate_update_and_confirm()
                time.sleep(60)
            elif current_minute > 1800 or current_minute < 800:
                time.sleep(60*60)
            else:
                time.sleep(60)
        else:
            time.sleep(60*60*4)

if __name__ == '__main__':
    run_update_data()





