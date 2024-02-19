#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/24 9:03
# @Author  : Suying
# @Site    : 
# @File    : account_recorder.py
import time
import os

from util.file_location import FileLocation
from record.multi_strategy_perf import MultiStrategyPerf
from record.talang_recorder import TalangRecorder
from record.panlan1_tinglian2_recorder import PanlanTinglianRecorder
from record.nongchao_recorder import NongchaoRecorder
from util.send_email import Mail, R
from util.trading_calendar import TradingCalendar


def account_recorder(date=None, adjust='导出单', if_last_trading_day=False):
    sep = '*' * 25
    print(f"\n{sep * 2} Update Account Recorder{adjust} {sep * 2}")

    formatted_date = time.strftime('%Y%m%d') if date is None else date
    last_trading_day = TradingCalendar().get_n_trading_day(formatted_date, -1).strftime('%Y%m%d')
    date_to_update = last_trading_day if if_last_trading_day else formatted_date

    monitor_dir = FileLocation.remote_monitor_dir
    account_path = rf'{monitor_dir}\衍舟策略观察.xlsx'
    multi_strategy_path = rf'{monitor_dir}\多策略超额.xlsx'
    monitor_path = rf'{monitor_dir}\monitor_{date_to_update}.xlsx'
    if not if_last_trading_day:
        print(f'{sep} Update Multi-Strategy Performance {sep}')
        MultiStrategyPerf(
            account_path=multi_strategy_path,
            monitor_path=monitor_path,
            date=date_to_update,
        ).update()

    if adjust == '对账单':
        Mail().receive(save_dir=rf'{os.path.expanduser("~")}\Desktop\Data\Save\账户对账单')

    print(f'{sep} Update Fund Record {sep}')
    update_fund_recorder(account_path, monitor_path, date_to_update, adjust)
    send_email(account_path, date_to_update, adjust)


def update_fund_recorder(account_path, monitor_path, date_to_update, adjust):
    TalangRecorder(account_path=account_path, monitor_path=monitor_path, date=date_to_update, adjust=adjust).update()
    NongchaoRecorder(account_path=account_path, date=date_to_update, adjust=adjust).record_nongchao()
    PanlanTinglianRecorder(account_path=account_path, account='盼澜1号', date=date_to_update,
                           adjust=adjust).record_account()
    # PanlanTinglianRecorder(account_path=account_path, account='听涟2号', date=date_to_update,
    #                        adjust=adjust).record_account()


def send_email(account_path, date_to_update, adjust):
    file = date_to_update + '导出单' if adjust == '导出单' else date_to_update + '对账单'
    content = f"""
        <table width="800" border="0" cellspacing="0" cellpadding="4">
        <tr>
        <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>{file}衍舟策略观察</b></td>
        </tr>
        <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
        <p><b>文件路径:</b></p>
        {account_path}
        <p><b>更新内容:</b></p>
        <p>更新踏浪1号、踏浪2号、踏浪3号、盼澜1号、听涟2号、弄潮1号、弄潮2号的资产信息</p>
        """
    Mail().send(
        subject=f'[衍舟策略观察] {file} 更新完成',
        body_content=content,
        attachs=[account_path],
        receivers=R.department['research'] + R.department['admin'],
    )
