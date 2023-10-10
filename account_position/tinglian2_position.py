#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/22 17:36
# @Author  : Suying
# @Site    : 
# @File    : tinglian2_position.py
import time
import pandas as pd
from file_location import FileLocation as FL


class Tinglian2Position():
    def __init__(self, date=None):
        formatted_date = time.strftime('%Y%m%d') if date is None else pd.to_datetime(date).strftime("%Y%m%d")
        self.tinglian2_actual_pos_path = rf"{FL.account_info_dir_dict['tinglian2']}/310310300343_RZRQ_POSITION.{formatted_date}.csv"
        self.tinglian2_target_pos_path = rf'{FL.remote_target_pos_dir}/tag_pos_310310300343_RZRQ_{formatted_date}.csv'

    def get_tinglian2_actual_position(self):
        try:
            actual_df = pd.read_csv(
                self.tinglian2_actual_pos_path,
                encoding='gbk',
            ).astype({'证券代码': str, '证券名称': str, '持仓数量': 'Int64', '市值': 'float64'})

            actual_df = actual_df.rename(columns={'证券代码': '代码', '证券名称': '名称', '持仓数量':
                '实际'}).set_index('代码')

            actual_df = actual_df[['名称', '实际', '市值']]
            return actual_df[actual_df['实际'] != 0]
        except Exception as e:
            print(e)
            print(f'Error:听涟2号实际持仓数据获取失败，请检查{self.tinglian2_actual_pos_path}文件是否存在，两分钟后重试')
            time.sleep(120)
            self.get_tinglian2_actual_position()

    def get_tinglian2_target_position(self):
        try:
            target_df = pd.read_csv(
                self.tinglian2_target_pos_path,
                header=0,
                index_col=False,
                names=['代码', '目标'],
                dtype={'代码': str, '目标': int},
            ).set_index('代码')
            target_df.index = target_df.index.str[2:]
            return target_df
        except Exception as e:
            print(e)
            print(f'Error:听涟2号目标持仓数据获取失败，请检查{self.tinglian2_target_pos_path}文件是否存在，两分钟后重试')
            time.sleep(120)
            self.get_tinglian2_target_position()
