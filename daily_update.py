# -*- coding: utf-8 -*-
# @Time    : 2023/8/10 9:03
# @Author  : Youwei Wu, Suying Zhou
# @File    : daily_update.py
# @Software: PyCharm

import time

from choice.c_st_list_updater import ST_List_Updater
from choice.c_kc50_weight_updater import KC50WeightUpdater
from choice.kc50_composition import download_check_kc50_composition
from t.ts_kline_updater import KlineUpdater
from t.ts_raw_daily_bar_updater import RawdailyBarUpdater

from record.account_recorder import account_recorder
from performance_analysis.strategy_review import send_strategy_review
from util.trading_calendar import TradingCalendar

from regular_update.equity_check import send_equity_check
from regular_update.live_virtual_kline import gen_live_virtual_kline
from regular_update.position_check import send_position_check
from regular_update.risk_exposure import send_risk_exposure
from regular_update.monitor import Monitor
# from regular_update.tick_check import Tick
from regular_update.rzrq_limit import download_rzrq_limit_file
from product_ret_analysis.product_ret_decomposition import ProductRetDecomposition
from regular_update.position_weight_check import check_pos_weight

def auto_update():
    while True:
        today = time.strftime('%Y%m%d')  # 每次循环重新记录下
        if today in TradingCalendar.trading_calendar:
            run_daily_update()
        else:
            print(time.strftime('%X'),
                  f'Today {today} is not trading day, sleep 12 hours.')
            time.sleep(12 * 60 * 60)


def run_daily_update():
    current_minute = int(time.strftime('%H%M'))
    if current_minute == 730:
        send_equity_check()
        account_recorder(adjust='对账单', if_last_trading_day=True)

    elif current_minute == 830:
        download_rzrq_limit_file()

    elif current_minute == 1400:
        ST_List_Updater().st_list_update_and_confirm()
        download_check_kc50_composition()

    elif current_minute == 1429:
        gen_live_virtual_kline(current_minute, execute_min=1430)

    elif current_minute == 1444:
        gen_live_virtual_kline(current_minute, execute_min=1445)

    elif current_minute == 1453:
        send_position_check()

    elif current_minute == 1501:
        send_position_check()
        Monitor().update()
        account_recorder()
        check_pos_weight()

    elif current_minute == 1630:
        update_data_after_close()
        send_strategy_review()
        ProductRetDecomposition().gen_email()
        # Tick().check_daily()

    elif current_minute > 1700:
        send_risk_exposure()

    elif current_minute % 5 == 0:
        print(time.strftime('%x %X'))

    time.sleep(60)


def update_data_after_close():
    KC50WeightUpdater().kc50_weight_update_and_confirm()
    RawdailyBarUpdater().update_and_confirm_raw_daily_bar()
    KlineUpdater().update_confirm_adjusted_kline()


if __name__ == '__main__':
    # auto_update()
    # RawdailyBarUpdater().update_and_confirm_raw_daily_bar()
    # KlineUpdater().update_confirm_adjusted_kline()
    send_strategy_review()
    ProductRetDecomposition().gen_email()
