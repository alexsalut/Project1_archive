#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/22 16:00
# @Author  : Suying
# @Site    : 
# @File    : account_monitor.py

# 目前日常滚动更新的是盼澜1和听涟2的账户盈亏情况
import time
from util.file_location import FileLocation as FL
from rolling_check.account_info import output_account_pl
from util.trading_calendar import TradingCalendar as TC


def account_monitor():
    while True:
        if TC().check_is_trading_day():
            current_minute = int(time.strftime('%H%M'))
            if 900 < current_minute < 1600:
                record_account_info()
            else:
                time.sleep(60)


def record_account_info(date=None):
    save_path = rf'{FL().remote_monitor_dir}/实时盈亏.txt'
    with open(save_path, 'r+') as f:
        f.truncate(0)
        f.write(output_account_pl('panlan1', date))
        f.write(output_account_pl('tinglian2', date))
        f.flush()


if __name__ == '__main__':
    account_monitor()


