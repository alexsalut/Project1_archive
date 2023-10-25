#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/24 15:13
# @Author  : Suying
# @Site    : 
# @File    : account_adjust.py

import time
import xlwings as xw
import os
from file_location import FileLocation as FL
from record.cnn_recorder import Cnn_Recorder
from record.talang_recorder import TalangRecorder
from record.panlan1_tinglian2_recorder import PanlanTinglianRecorder
from record.remote_recorder import update_account_remote
from util.utils import send_email, SendEmailInfo
from util.trading_calendar import TradingCalendar as TC

def adjust_account(date=None):
    formatted_date = date if date is not None else time.strftime('%Y%m%d')
    last_trading_day = TC().get_n_trading_day(formatted_date,-1).strftime('%Y%m%d')
    account_path = rf'{FL().monitor_dir}\cnn策略观察_{last_trading_day}.xlsx'
    remote_account_path = rf'{FL().remote_monitor_dir}\cnn策略观察.xlsx'

    TalangRecorder(account_path=account_path, date=date).record_talang()
    PanlanTinglianRecorder(account_path=account_path, account='panlan1', date=last_trading_day).record_account()
    PanlanTinglianRecorder(account_path=account_path, account='tinglian2', date=last_trading_day).record_account()
    update_account_remote(account_path=account_path, remote_account_path=remote_account_path)