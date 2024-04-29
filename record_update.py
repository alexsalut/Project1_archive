#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/4/3 17:16
# @Author  : Suying
# @Site    : 
# @File    : record_update.py

import time

from choice.c_kc50_weight_updater import KC50WeightUpdater
from record.account_recorder import account_recorder
from performance_analysis.strategy_review import send_strategy_review
from util.trading_calendar import TradingCalendar
from regular_update.equity_check import send_equity_check
from regular_update.position_check import send_position_check
from regular_update.risk_exposure import send_risk_exposure
from regular_update.monitor import Monitor
from product_ret_analysis.product_ret_decomposition import ProductRetDecomposition
from regular_update.med_kc_stock_pred import send_med_stock_list
from others.zz500_monitor import update_zz500_next_trading_day_pos
from record.zz500_multi_strategy_update import ZZ500MultiStrategyPerf
from choice.c_st_list_updater import ST_List_Updater
from rice_quant.update_conversion_price import download_conversion_price



def record_update():
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
    if current_minute == 830:
        send_equity_check()
        account_recorder(adjust='对账单', if_last_trading_day=True)

    elif current_minute == 1457:
        send_position_check()
        KC50WeightUpdater().kc50_weight_update_and_confirm()
        send_med_stock_list()

    elif current_minute == 1502:
        send_position_check()
        Monitor().update()
        account_recorder()
        update_zz500_next_trading_day_pos()

    elif current_minute == 1630:
        ZZ500MultiStrategyPerf().update()
        send_strategy_review()
        ProductRetDecomposition(stock_list=['踏浪1号', '盼澜1号'], option_list=['盼澜1号']).gen_email()
        ST_List_Updater().st_list_update_and_confirm()

    elif current_minute > 1700:
        download_conversion_price()
        send_risk_exposure()

    elif current_minute % 5 == 0:
        print(time.strftime('%x %X'))
        time.sleep(60)


if __name__ == '__main__':
    record_update()
