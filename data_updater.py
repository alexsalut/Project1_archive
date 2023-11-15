# -*- coding: utf-8 -*-
# @Time    : 2023/8/10 9:03
# @Author  : Youwei Wu, Suying Zhou
# @File    : data_updater.py
# @Software: PyCharm

import time

from choice.c_st_list_updater import ST_List_Updater
from choice.c_kc50_weight_updater import KC50WeightUpdater
from choice.kc50_composition import download_check_kc50_composition

from t.ts_kline_updater import KlineUpdater
from t.ts_raw_daily_bar_updater import RawDailyBarUpdater

from position.position_check import send_position_check

from record.account_recorder import account_recorder
from monitor import Monitor

from rice_quant.risk_exposure import send_fund_portfolio_exposure
from rice_quant.live_kline_updater import gen_ricequant_virtual_kline, gen_stock_list
from performance_analysis.strategy_review import send_strategy_review

from util.trading_calendar import TradingCalendar
from util.utils import SendEmailInfo
from tick_check.tick_check import Tick
from account_check.account_cross_check import AccountCheck


def auto_update():
    while True:
        today = time.strftime('%Y%m%d')  # 每次循环重新记录下
        if today in TradingCalendar.trading_calendar:
            print(time.strftime('%X'))
            run_daily_update()
        else:
            print(time.strftime('%X'),
                  f'Today {today} is not trading day, sleep 12 hours.')
            time.sleep(12 * 60 * 60)


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
        send_position_check(receivers)

    elif current_minute == 1505:
        Monitor().update()
        account_recorder()

    elif current_minute == 1630:
        update_data_after_close()
        send_strategy_review()
        Tick().check_daily()

    elif current_minute > 1700:
        send_fund_portfolio_exposure()

    time.sleep(60)


def gen_quick_virtual_kline(current_minute):
    date = time.strftime('%Y%m%d')
    stock_list = gen_stock_list(date)

    while int(time.strftime('%H%M')) == current_minute:
        print(time.strftime('%X'), 'Wait for update!')
        time.sleep(0.1)
    gen_ricequant_virtual_kline(stock_list, date)


def update_data_after_close():
    KC50WeightUpdater().kc50_weight_update_and_confirm()
    RawDailyBarUpdater().update_and_confirm_raw_daily_bar()
    KlineUpdater().update_confirm_adjusted_kline()


if __name__ == '__main__':
    auto_update()
