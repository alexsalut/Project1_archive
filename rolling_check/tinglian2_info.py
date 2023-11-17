#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/23 17:27
# @Author  : Suying
# @Site    : 
# @File    : tinglian2_info.py
import time
import pandas as pd
from util.file_location import FileLocation as FL

tinglian2_account_dir = FL().account_info_dir_dict['tinglian2']

def get_tinglian2_raw_info(date=None):
    date = time.strftime('%Y%m%d') if date is None else pd.to_datetime(date).strftime("%Y%m%d")
    option_s = pd.read_csv(rf'{tinglian2_account_dir}\310317000090_OPTION_FUND.{date}.csv',
                           encoding='gbk',
                           index_col=False).iloc[0]
    stock_s = pd.read_csv(rf'{tinglian2_account_dir}\310310300343_RZRQ_FUND.{date}.csv', encoding='gbk',
                          index_col=False).iloc[0]
    info_dict = {
        'option equity': option_s['资产总值'],
        'stock equity': stock_s['资产总值'] - stock_s['总负债'],
    }
    return info_dict

if __name__ == '__main__':
    get_tinglian2_raw_info()



