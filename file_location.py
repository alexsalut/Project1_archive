#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/22 9:55
# @Author  : Suying
# @Site    : 
# @File    : file_location.py

class FileLocation:
# 账户信息文件路径
    account_info_dir_dict = {
        'talang2': r'\\192.168.1.116\trade\broker\qmt_gf\account\Stock',
        'talang3': r'\\192.168.1.116\trade\broker\iQuant\account\Stock',
        'talang1': r'\\192.168.1.116\trade\broker\cats\account',
        'panlan1': r'\\192.168.1.116\trade\broker\cats\account',
        'tinglian2': r'\\192.168.1.116\trade\broker\emc\account'

    }


# 账户代码
    stock_account_code_dict = {
        'talang1': 4089106,  # cats
        'talang2': 14748783, # qmt
        'talang3': 190000612973, #iQuant
        'panlan1': 4082225, # cats
    }

    option_account_code_dict = {
        'panlan1': 9008023342, # cats
    }




# cnn策略观察文件路径， monitor文件路径
    monitor_dir = r'C:\Users\Yz02\Desktop\strategy_update'
    remote_monitor_dir = r'\\192.168.1.116\target_position\monitor'
    remote_summary_dir = r'\\192.168.1.116\target_position\summary'
    remote_target_pos_dir = r'\\192.168.1.116\trade\target_position\account'

# choice终端获取数据存储路径
    kc50_weight_dir = r"\\192.168.1.116\choice\reference\index_weight\sh000688\cache"
    st_list_path = r'\\192.168.1.116\kline\st_list.csv'
    turnover_dir = "C:/Users/Yz02/Desktop/Data/Choice"
    kc50_composition_dir = r'\\192.168.1.116\choice\reference\sh000688'

# 米匡数据存储路径
    exposure_dir = r'\\192.168.1.116\trade\target_position\exposure'

# tushare数据存储路径
    raw_daily_dir = r"\\192.168.1.116\tushare\price\daily\raw"
    kline_path = r"\\192.168.1.116\kline\qfq_kline_product.pkl"

# web期货数据存储路径
    future_dir = r'\\192.168.1.116\cffe'







