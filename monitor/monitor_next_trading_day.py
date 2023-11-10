#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/25 13:45
# @Author  : Suying
# @Site    : 
# @File    : monitor_next_trading_day.py

import os
import time
import xlwings as xw
import pandas as pd
from util.send_email import Mail, R
from util.utils import retry_save_excel
from util.trading_calendar import TradingCalendar as TC

def update_monitor_next_trading_day(date, monitor_path, remote_monitor_dir, monitor_dir, remote_summary_dir):
    formatted_date = pd.to_datetime(date).strftime("%Y%m%d")
    next_trading_day = TC().get_n_trading_day(formatted_date,1).strftime('%Y%m%d')
    local_path = rf'{monitor_dir}/monitor_{next_trading_day}_formula.xlsx'
    if os.path.exists(local_path):
        print('[Monitor Next trading day update]File already exists')

    else:
        try:
            app = xw.App(visible=False, add_book=False)
            app.display_alerts = False
            app.screen_updating = False
            wb = app.books.open(monitor_path)
            sheet = wb.sheets[0]

            sheet['B1'].value = next_trading_day
            stock_shares_df, tag_pos_df = renew_stock_list(remote_summary_dir, formatted_date)
            for index in tag_pos_df.index:
                sheet[f'B{index + 5}'].value = tag_pos_df.loc[index, 'index']
            for index in stock_shares_df.index:
                sheet[f'A{index + 98}'].value = stock_shares_df.loc[index, 'index']
                sheet[f'B{index + 98}'].formula = f'=EM_S_INFO_NAME(A{index + 98})'
                sheet[f'C{index + 98}'].value = stock_shares_df.loc[index, '0']
                sheet[f'D{index + 98}'].formula = f'=EM_S_INFO_INDUSTRY_SW2021(A{index + 98},"1")'
                sheet[f'E{index + 98}'].formula = f'=EM_S_FREELIQCI_VALUE(A{index + 98},B1,100000000)'
                sheet[f'F{index + 98}'].formula = f'=EM_S_VAL_MV2(A{index + 98},B1,100000000)'
                sheet[f'G{index + 98}'].formula = f'=RTD("em.rtq",,A{index + 98},"Time")'
                sheet[f'H{index + 98}'].formula = f'=RTD("em.rtq",,A{index + 98},"DifferRange")'

            rows_to_delete = range(98 + len(stock_shares_df), 180)
            for row in rows_to_delete:
                sheet.api.Rows(row).Delete()

            retry_save_excel(wb=wb, file_path=local_path)

            remote_path = rf'{remote_monitor_dir}/monitor_{next_trading_day}_formula.xlsx'
            retry_save_excel(wb=wb, file_path=remote_path)
            wb.close()
            app.quit()
            print('[Monitor Next trading day update]Updated successfully')


            Mail().send(subject=f'Monitor next trading day updated, archive today monitor in 2 min',
                        body_content='',
                        receivers=[R.staff['zhou']]
                        )

            time.sleep(120)

        except Exception as e:
            print(e)
            print('[Monitor Next trading day update]Update failed, retry in 10 seconds')
            time.sleep(10)
            update_monitor_next_trading_day()


def renew_stock_list(remote_summary_dir, today):
    try:
        stock_shares_df = pd.read_csv(
            rf'{remote_summary_dir}/stock_shares_{today}.csv', index_col=0,
        ).reset_index(drop=False)
        tag_pos_df = pd.read_csv(
            rf'{remote_summary_dir}/tag_pos_{today}.csv', index_col=0,
        ).reset_index(drop=False)
        print('[Next trading day stock list] Updated successfully')
        return stock_shares_df, tag_pos_df
    except Exception as e:
        print(e)
        print('[Next trading day stock list]Update failed, retry in 20 seconds')
        time.sleep(20)
        renew_stock_list(remote_summary_dir, today)


if __name__ == '__main__':
    monitor_path = r'C:\Users\Yz02\Desktop\strategy_update\monitor_test.xlsx'
    remote_monitor_dir = r'\\192.168.1.116\target_position\monitor'
    monitor_dir = r'C:\Users\Yz02\Desktop\strategy_update'
    remote_summary_dir = r'\\192.168.1.116\target_position\summary'
    update_monitor_next_trading_day(
        date='20231107',
        monitor_path=monitor_path,
        remote_monitor_dir=remote_monitor_dir,
        monitor_dir=monitor_dir,
        remote_summary_dir=remote_summary_dir
    )