#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/25 13:45
# @Author  : Suying
# @Site    : 
# @File    : monitor_next_trading_day.py

import time
import xlwings as xw
import pandas as pd
from util.utils import send_email, retry_save_excel
from util.trading_calendar import TradingCalendar as TC

def update_monitor_next_trading_day(date, monitor_path, remote_monitor_dir, monitor_dir, remote_summary_dir):
    formatted_date = pd.to_datetime(date).strftime("%Y%m%d")
    next_trading_day = TC().get_n_trading_day(formatted_date,1).strftime('%Y%m%d')

    try:
        app = xw.App(visible=False, add_book=False)
        app.display_alerts = False
        app.screen_updating = False
        wb = app.books.open(monitor_path)
        sheet = wb.sheets[0]

        sheet['B1'].value = next_trading_day
        stock_shares_df, tag_pos_df = renew_stock_list(remote_summary_dir, formatted_date)
        for index in tag_pos_df.index:
            sheet[f'B{index + 4}'].value = tag_pos_df.loc[index, 'index']
        for index in stock_shares_df.index:
            sheet[f'A{index + 57}'].value = stock_shares_df.loc[index, 'index']
            sheet[f'B{index + 57}'].formula = f'=EM_S_INFO_NAME(A{index + 57})'
            sheet[f'C{index + 57}'].value = stock_shares_df.loc[index, '0']
            sheet[f'D{index + 57}'].formula = f'=EM_S_INFO_INDUSTRY_SW2021(A{index + 57},"1")'
            sheet[f'E{index + 57}'].formula = f'=EM_S_FREELIQCI_VALUE(A{index + 57},B1,100000000)'
            sheet[f'F{index + 57}'].formula = f'=EM_S_VAL_MV2(A{index + 57},B1,100000000)'
            sheet[f'G{index + 57}'].formula = f'=RTD("em.rtq",,A{index + 57},"Time")'
            sheet[f'H{index + 57}'].formula = f'=RTD("em.rtq",,A{index + 57},"DifferRange")'

        rows_to_delete = range(57 + len(stock_shares_df), 107)
        for row in rows_to_delete:
            sheet.api.Rows(row).Delete()

        local_path = rf'{monitor_dir}/monitor_{next_trading_day}_formula.xlsx'
        retry_save_excel(wb=wb, file_path=local_path)

        remote_path = rf'{remote_monitor_dir}/monitor_{next_trading_day}_formula.xlsx'
        retry_save_excel(wb=wb, file_path=remote_path)
        wb.close()
        app.quit()
        print('[Monitor Next trading day update]Updated successfully')
        send_email(
            subject=f'Monitor next trading day updated, archive today summary now',
            content='',
            receiver='zhou.sy@yz-fund.com.cn'
        )

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