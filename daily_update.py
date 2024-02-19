# -*- coding: utf-8 -*-
# @Time    : 2023/8/10 9:03
# @Author  : Youwei Wu, Suying Zhou
# @File    : daily_update.py
# @Software: PyCharm

import time

from choice.c_kc50_weight_updater import KC50WeightUpdater
from t.ts_kline_updater import KlineUpdater
from t.ts_raw_daily_bar_updater import RawdailyBarUpdater
from record.account_recorder import account_recorder
from performance_analysis.strategy_review import send_strategy_review
from util.trading_calendar import TradingCalendar
from regular_update.equity_check import send_equity_check
from regular_update.position_check import send_position_check
from regular_update.risk_exposure import send_risk_exposure
from regular_update.monitor import Monitor
from regular_update.rzrq_limit import download_rzrq_limit_file
from product_ret_analysis.product_ret_decomposition import ProductRetDecomposition
from regular_update.med_kc_stock_pred import send_med_stock_list


def auto_update():
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
    if current_minute == 730:
        send_equity_check()
        account_recorder(adjust='对账单', if_last_trading_day=True)

    elif current_minute == 830:
        download_rzrq_limit_file()

    elif current_minute == 1457:
        send_position_check()
        KC50WeightUpdater().kc50_weight_update_and_confirm()
        send_med_stock_list()

    elif current_minute == 1502:
        send_position_check()
        Monitor().update()
        account_recorder()

    elif current_minute == 1619:
        update_data_after_close()
        send_strategy_review()
        ProductRetDecomposition().gen_email()

    elif current_minute > 1700:
        send_risk_exposure()

    elif current_minute % 5 == 0:
        print(time.strftime('%x %X'))

    time.sleep(60)


def update_data_after_close():
    RawdailyBarUpdater().update_and_confirm_raw_daily_bar()
    KlineUpdater().update_confirm_adjusted_kline()


if __name__ == '__main__':
    auto_update()
