#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/24 9:03
# @Author  : Suying
# @Site    : 
# @File    : product_recorder.py
import time
import os
import shutil

import pandas as pd
import rqdatac as rq
from util.file_location import FileLocation
from record.talang_recorder import TalangRecorder
from record.panlan1_tinglian2_recorder import PanlanTinglianRecorder
from record.nongchao_recorder import NongchaoRecorder
from util.send_email import Mail, R
from util.trading_calendar import TradingCalendar
from record.get_product_clearing import SettleInfo
from record.tinglian1_recorder import Tinglian1Recorder


def product_recorder(date=None,
                     adjust='导出单',
                     if_last_trading_day=False,
                     product_list=None):
    rq.init()
    formatted_date = time.strftime('%Y%m%d') if date is None else pd.to_datetime(date).strftime('%Y%m%d')
    last_trading_day = TradingCalendar().get_n_trading_day(formatted_date, -1).strftime('%Y-%m-%d')
    date_to_update = last_trading_day if if_last_trading_day else formatted_date

    monitor_dir = FileLocation.remote_monitor_dir
    account_path = rf'{monitor_dir}\衍舟策略观察.xlsx'
    monitor_path = rf'{monitor_dir}\monitor_{date_to_update}.xlsx'

    to_update_product_lst = ['踏浪1号', '踏浪2号', '踏浪3号', '盼澜1号', '听涟2号', '弄潮1号', '弄潮2号', '听涟1号'] \
        if product_list is None else product_list

    sep = '*' * 25
    print(f"\n{sep * 2} Update Account Recorder {adjust} {date_to_update}  {sep * 2}")

    if adjust == '对账单':
        file_list = SettleInfo(date=date_to_update).file_path_list
        to_download_files = [os.path.basename(file) for file in file_list if not os.path.exists(file)]
        if to_download_files:
            Mail().receive(save_dir=rf'{os.path.expanduser("~")}\Desktop\Data\Save\账户对账单',
                           date_range=[6, 1],
                           file_list=to_download_files)

    print(f'{sep} Update Fund Record {date_to_update}{sep}')
    update_fund_recorder(account_path,
                         monitor_path,
                         date_to_update,
                         adjust,
                         product_list=to_update_product_lst)
    try:
        shutil.copy(account_path, account_path.replace('策略观察', '策略观察备份'))
    except Exception as e:
        print(e)
    send_email(account_path, date_to_update, adjust, to_update_product_lst)


def update_fund_recorder(account_path,
                         monitor_path,
                         date_to_update,
                         adjust,
                         product_list):
    if '听涟1号' in product_list:
        Tinglian1Recorder(account_path=account_path, date=date_to_update, adjust=adjust).update()
    if '盼澜1号' in product_list:
        PanlanTinglianRecorder(account_path=account_path, account='盼澜1号', date=date_to_update,
                               adjust=adjust).update()
    if '听涟2号' in product_list:
        PanlanTinglianRecorder(account_path=account_path, account='听涟2号', date=date_to_update,
                               adjust=adjust).update()

    talang_lst = [product for product in product_list if '踏浪' in product]
    if talang_lst:
        TalangRecorder(account_path=account_path,
                       monitor_path=monitor_path,
                       date=date_to_update,
                       adjust=adjust,
                       product_list=talang_lst).update()

    nongchao_lst = [product for product in product_list if '弄潮' in product]
    if nongchao_lst:
        NongchaoRecorder(account_path=account_path,
                         date=date_to_update,
                         adjust=adjust).update()


def send_email(account_path, date_to_update, adjust, product_list):
    file = date_to_update + '导出单' if adjust == '导出单' else date_to_update + '对账单'
    product_string = '、'.join(product_list)
    content = f"""
        <table width="800" border="0" cellspacing="0" cellpadding="4">
        <tr>
        <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>{file}衍舟策略观察</b></td>
        </tr>
        <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
        <p><b>文件路径:</b></p>
        {account_path}
        <p><b>更新内容:</b></p>  
        <p>更新{product_string}的资产信息</p>
        """
    Mail().send(
        subject=f'[衍舟策略观察] {file} 更新完成',
        body_content=content,
        attachs=[account_path],
        receivers=R.department['research'] + R.department['admin'],
    )
