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
from util.trading_calendar import TradingCalendar


def update_monitor_next_trading_day(date, t0_monitor_path, remote_monitor_dir, remote_summary_dir):
    formatted_date = pd.to_datetime(date).strftime("%Y%m%d")
    next_trading_day = TradingCalendar().get_n_trading_day(formatted_date, 1).strftime('%Y%m%d')
    stock_shares_df, tag_pos_df = renew_stock_list(remote_summary_dir, formatted_date)

    if os.path.exists(t0_monitor_path):
        """
        表格内容
        前三行是三个产品，
        第四行是子策略持仓tag_pos_df的columns，
        tag_pos_df下面空两行，
        跟着是stock_shares_df的columns.
        """
        app = xw.App(visible=False, add_book=False)  # 新建一个处理excel的进程
        app.display_alerts = False  # 关闭一些提示信息，可以加快运行速度
        app.screen_updating = False  # 关闭工作表内容显示，可以加快运行速度
        wb = app.books.open(t0_monitor_path)
        sheet = wb.sheets[0]

        # tag_pos_df第一行在表格中的行数
        row0 = 5
        # tag_pos_df最后一行在表格中的行数
        row1 = 4 + len(tag_pos_df)
        # stock_shares_df第一行在表格中的行数
        row2 = 4 + len(tag_pos_df) + 4
        # stock_shares_df最后一行在表格中的行数
        row3 = 4 + len(tag_pos_df) + 4 + len(stock_shares_df)

        # title
        sheet['B1'].value = next_trading_day
        # tag_pos_df
        sheet[f'B{row0}:B{row1}'].value = tag_pos_df['index']
        # stock_shares_df
        sheet[f'A{row2}:A{row3}'].value = stock_shares_df['index']
        sheet[f'C{row2}:C{row3}'].value = stock_shares_df['0']
        for order in range(row2, row3 + 1):
            sheet[f'B{order}'].formula = f'=EM_S_INFO_NAME(A{order})'
            sheet[f'D{order}'].formula = f'=EM_S_INFO_INDUSTRY_SW2021(A{order},"1")'
            sheet[f'E{order}'].formula = f'=EM_S_FREELIQCI_VALUE(A{order},B1,100000000)'
            sheet[f'F{order}'].formula = f'=EM_S_VAL_MV2(A{order},B1,100000000)'
            sheet[f'G{order}'].formula = f'=RTD("em.rtq",,A{order},"Time")'
            sheet[f'H{order}'].formula = f'=RTD("em.rtq",,A{order},"DifferRange")'

        rows_to_delete = range(row3, 180)
        for row in rows_to_delete:
            sheet.api.Rows(row).Delete()

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

    else:
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
