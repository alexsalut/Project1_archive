#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/28 10:18
# @Author  : Suying
# @Site    : 
# @File    : talang1_position.py
import pandas as pd
import time
from file_location import FileLocation as FL

class Talang1Position:
    def __init__(self, date=None):
        formatted_date1 = time.strftime('%Y%m%d') if date is None else pd.to_datetime(date).strftime("%Y%m%d")
        formatted_date2 = time.strftime('%Y-%m-%d') if date is None else pd.to_datetime(date).strftime("%Y-%m-%d")
        account_dir = FL.account_info_dir_dict['talang1']
        self.talang1_actual_pos_path = rf'{account_dir}/StockPosition_{formatted_date2}.csv'
        self.talang1_target_pos_path = rf'{FL.remote_target_pos_dir}/tag_pos_4089106_{formatted_date1}.csv'

    def get_talang1_actual_position(self):
        try:
            actual_df = pd.read_csv(
                self.talang1_actual_pos_path,
                index_col='代码',
                dtype={'代码': str, '当前余额': 'Int64', '参考市值': 'Float64', '名称': str},
            ).rename(columns={'当前余额': '实际', '参考市值': '市值'}).query('账户==4089106')[['实际', '市值', '名称']]
            return actual_df[actual_df['实际'] != 0]
        except Exception as e:
            print(e)
            print(f'Error:踏浪1号实际持仓数据获取失败，请检查{self.talang1_actual_pos_path}文件是否存在，两分钟后重试')
            time.sleep(120)
            self.get_talang1_actual_position()

    def get_talang1_target_position(self):
        try:
            target_df = pd.read_csv(
                self.talang1_target_pos_path,
                index_col=False,
                header=0,
                names=['代码', '目标'],
                dtype={'代码': str, '目标': 'Int64'},
            ).set_index('代码')
            target_df.index = target_df.index.str[2:]
            return target_df
        except Exception as e:
            print(e)
            print(f'Error:盼澜1号目标持仓数据获取失败，请检查{self.talang1_target_pos_path}文件是否存在，两分钟后重试')
            time.sleep(120)
            self.get_talang1_target_position()