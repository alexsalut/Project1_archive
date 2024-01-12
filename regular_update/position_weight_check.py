#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/12/14 13:20
# @Author  : Suying
# @Site    : 
# @File    : position_weight_check.py
import time
import rqdatac as rq

from regular_update.position_check import AccountPosition
from regular_update.monitor import Monitor
from util.send_email import Mail, R
from util.trading_calendar import TradingCalendar as tc


def check_pos_weight(account='踏浪1号', date=None):
    date = date if date is not None else time.strftime('%Y%m%d')
    check_df = check_position_weight(account, date)

    def highlight_diff(s):
        if abs(s) > 0.2:
            return f'background-color: lightblue'
        else:
            return ''

    check_df = check_df.style.applymap(highlight_diff, subset=['差值%'])
    styled_df = check_df.format('{:.2f}')
    df_text = styled_df.to_html(float_format='%.2f')

    subject = rf'[踏浪1号持仓偏移检查{date}]'
    content = fr"""
            <table width="800" border="0" cellspacing="0" cellpadding="4">
            <tr>
            <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>踏浪1号股票权重偏移情况:</b></td>
            </tr>
            <td bgcolor="#EFEBDE" height="100" style="font-size:13px">

            <html><head><style>table.bordered-table {{ border-collapse: seperate; width: 100%; }} 
            table.bordered-table, th, td {{ border: 1px solid black; }} th, td {{ padding: 8px;}}</style> 
            </head><body>{df_text}</body></html> 

            """
    Mail().send(subject=subject, body_content=content, receivers=R.department['research'])


def check_position_weight(account='踏浪1号', date=None):
    date = date if date is not None else time.strftime('%Y%m%d')
    monitor_pos = Monitor().collect_related_data(today=date)['tag_pos_df'].set_index('index', drop=True)
    monitor_pos = monitor_pos.query('strategy!="I10R2_all_5"').reset_index(drop=False).groupby('index').count()
    monitor_pos.columns = ['理论']
    monitor_pos['理论'] = monitor_pos['理论'].div(monitor_pos['理论'].sum())
    monitor_pos.index = monitor_pos.index.astype(int).astype(str)

    actual_pos = AccountPosition(account, date).get_actual_position()
    actual_pos.index = actual_pos.index.astype(int).astype(str)
    actual_pos['实际'] = actual_pos['市值'].div(actual_pos['市值'].sum())

    pos_weight_df = actual_pos.merge(monitor_pos, left_index=True, right_index=True, how='outer').fillna(0)
    pos_weight_df['差值'] = pos_weight_df['实际'] - pos_weight_df['理论']
    pos_weight_df = pos_weight_df.sort_values(by='差值', ascending=False)

    pos_weight_df['名称'] = pos_weight_df.index.map(get_ticker_name(pos_weight_df.index.tolist()))
    pos_weight_df = pos_weight_df.set_index('名称', drop=True)
    pos_weight_df.index.name = None
    pos_weight_df = 100 * pos_weight_df.rename(columns={'实际': '实际%', '理论': '理论%', '差值': '差值%'})

    return pos_weight_df[['实际%', '理论%', '差值%']]


def get_ticker_name(ticker_list):
    rq.init()
    new_ticker_list = rq.id_convert(ticker_list)
    ticker_name = rq.instruments(new_ticker_list)
    name_dict = {ticker.order_book_id[:6]: ticker.symbol for ticker in ticker_name}
    return name_dict
