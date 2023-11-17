#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/22 9:55
# @Author  : Suying
# @Site    : 
# @File    : file_location.py

import os


class FileLocation:

    # 账户信息文件路径
    account_info_dir_dict = {
        '踏浪2号': r'\\192.168.1.116\trade\broker\qmt_gf\account\Stock',
        '踏浪3号': r'\\192.168.1.116\trade\broker\iQuant\account\Stock',
        '踏浪1号': r'\\192.168.1.116\trade\broker\cats\account',
        '盼澜1号': r'\\192.168.1.116\trade\broker\cats\account',
        '听涟2号 emc': r'\\192.168.1.116\trade\broker\emc\account',
        '听涟2号 cats': r'\\192.168.1.116\trade\broker\cats\account',
        '弄潮1号 cats': r'Z:\投研\数据\交易记录\nongchao\cats',
        '弄潮1号 matic': r'Z:\投研\数据\交易记录\nongchao\matic',
        '弄潮2号 matic': r'Z:\投研\数据\交易记录\nongchao\matic',
    }

    # 客户编号
    account_code = {
        '踏浪1号': 4089106,  # cats
        '踏浪2号': 14748783,  # qmt
        '踏浪3号': 190000612973,  # iQuant
        '盼澜1号': 4082225,  # cats
        '踏浪1号_credit': 4089106,  # cats
        '听涟2号': 310310300343,  # emc
        '弄潮1号 cats': 4069336,  # cats
        '弄潮1号 cats_HK': 7200001295,
    }

    # 资产账户
    option_account_code_dict = {
        '盼澜1号': 4082225,  # cats
        '听涟2号': 4088701,  # cats
    }

# 衍舟策略观察文件路径， monitor文件路径
    monitor_dir = rf'{os.path.expanduser("~")}\Desktop\strategy_update'
    remote_monitor_dir = r'\\192.168.1.116\target_position\monitor'
    remote_summary_dir = r'\\192.168.1.116\target_position\summary'
    remote_target_pos_dir = r'\\192.168.1.116\trade\target_position\account'

# choice终端获取数据存储路径
    kc50_weight_dir = r"\\192.168.1.116\choice\reference\index_weight\sh000688\cache"
    st_list_path = r'\\192.168.1.116\kline\st_list.csv'
    kc50_composition_dir = r'\\192.168.1.116\choice\reference\sh000688'

# RiceQuant数据存储路径
    exposure_dir = r'\\192.168.1.116\trade\target_position\exposure'

# tushare数据存储路径
    raw_daily_dir = r"\\192.168.1.116\tushare\price\daily\raw"
    kline_path = r"\\192.168.1.116\kline\qfq_kline_product.pkl"

# web期货数据存储路径
    future_dir = r'\\192.168.1.116\cffe'

# 结算单存储路径
    clearing_dir = rf'{os.path.expanduser("~")}\Desktop\Data\Save\账户对账单'
# 因子数据存储路径
    factor_dir = r'\\192.168.1.116\trade\cnn_factor'
