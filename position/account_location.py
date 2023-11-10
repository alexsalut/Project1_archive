#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/10 14:51
# @Author  : Suying
# @Site    : 
# @File    : account_location.py
import time
import pandas as pd
from file_location import FileLocation as FL
def get_account_location(date=None):
    formatted_date1 = time.strftime('%Y%m%d') if date is None else pd.to_datetime(date).strftime("%Y%m%d")
    formatted_date2 = time.strftime('%Y-%m-%d') if date is None else pd.to_datetime(date).strftime("%Y-%m-%d")
    account_position_dict = {}
    account_position_dict['panlan1'] = {
        'actual': rf"{FL.account_info_dir_dict['panlan1']}/CreditPosition_{formatted_date2}.csv",
        'target': rf'{FL.remote_target_pos_dir}/tag_pos_盼澜1号信用账户_{formatted_date1}.csv',
    }

    account_position_dict['tinglian2'] = {
        'actual': rf"{FL.account_info_dir_dict['tinglian2 emc']}/310310300343_RZRQ_POSITION.{formatted_date1}.csv",
        'target': rf'{FL.remote_target_pos_dir}/tag_pos_听涟2号信用账户_{formatted_date1}.csv',
    }

    account_position_dict['talang1'] = {
        'actual': rf"{FL.account_info_dir_dict['talang1']}/CreditPosition_{formatted_date2}.csv",
        'target': rf'{FL.remote_target_pos_dir}/tag_pos_踏浪1号信用账户_{formatted_date1}.csv',
    }

    return account_position_dict



