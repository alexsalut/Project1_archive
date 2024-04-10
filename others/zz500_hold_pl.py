#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/3/8 16:36
# @Author  : Suying
# @Site    : 
# @File    : zz500_hold_pl.py
import pandas as pd
import rqdatac as rq
from util.get_close_price import get_close_price


def get_talang2_putong_hold_pl(date):
    rq.init()
    last_trading_day = rq.get_previous_trading_date(date, 1).strftime('%Y%m%d')
    last_pos = get_talang2_putong_pos(last_trading_day).rename('持仓')
    code_list = rq.id_convert([code[2:] + '.' + code[:2].upper() for code in last_pos.index.tolist()])
    last_pos.index = code_list


    close = rq.get_price(code_list, start_date=date, end_date=date, fields=['close','prev_close']).droplevel(1)

    today_index_ret = rq.get_price_change_rate('000905.XSHG', start_date=date, end_date=date).iloc[0, 0]
    df = pd.concat([last_pos, close], axis=1).dropna()
    df['昨日市值'] = df['持仓'] * df['prev_close']
    df['当前市值'] = df['持仓'] * df['close']
    hold_pl = df['当前市值'].sum() - df['昨日市值'].sum()
    hold_pl_ret = hold_pl / df['昨日市值'].sum()
    excess_ret = hold_pl_ret - today_index_ret
    pl_s = pd.Series({'持有盈亏': hold_pl,
                      '持有盈亏率': hold_pl_ret,
                      '中证500收益率': today_index_ret,
                      '超额收益率': excess_ret}).rename(date)
    return pl_s


def get_talang2_putong_pos(date):
    path = rf'\\192.168.1.116\target_position\account\tag_pos_踏浪2号普通账户_{date}.csv'
    pos = pd.read_csv(path, index_col=0).iloc[:, 0]
    return pos



if __name__ == '__main__':
    data = []
    for date in ['20240307','20240308']:
        s = get_talang2_putong_hold_pl(date)
        data.append(s)
    df = pd.concat(data, axis=1)
    print(df)