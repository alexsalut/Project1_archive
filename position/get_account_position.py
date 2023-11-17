#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/10 14:30
# @Author  : Suying
# @Site    : 
# @File    : get_account_position.py
import time
import pandas as pd
from util.file_location import FileLocation as FL
from position.account_location import get_account_location


class AccountPosition:
    def __init__(self, account, date=None):
        self.account = account
        self.date = date if date is not None else time.strftime('%Y%m%d')
        self.col_dict = self.get_position_col()
        self.location_dict = get_account_location(self.date)[self.account]

    def get_target_position(self):
        try:
            target_df = pd.read_csv(
                self.location_dict['target'],
                index_col=False,
                header=0,
                names=['代码', '目标'],
                dtype={'代码': str, '目标': 'Int64'},
            ).set_index('代码')
            target_df.index = target_df.index.str[2:]
            return target_df
        except Exception as e:
            print(e)
            print(
                f'Error: {self.account}目标持仓数据获取失败，请检查{self.location_dict["target"]}文件是否存在，两分钟后重试')
            time.sleep(120)
            self.get_target_position()

    def get_actual_position(self):
        try:
            encoding = 'gbk' if self.account == '听涟2号' else None
            actual_df = pd.read_csv(
                self.location_dict['actual'],
                encoding=encoding,
            ).astype({
                self.col_dict['actual code']: str,
                self.col_dict['actual name']: str,
                self.col_dict['actual']: 'Int64',
                self.col_dict['actual market val']: 'float64',
            })
            actual_df = actual_df.rename(columns={
                self.col_dict['actual code']: '代码',
                self.col_dict['actual name']: '名称',
                self.col_dict['actual']: '实际',
                self.col_dict['actual market val']: '市值'}).set_index('代码')
            if 'actual account' in self.col_dict.keys():
                actual_df = actual_df.query(f'账户=={FL.account_code[self.account]}')
            actual_df = actual_df[['名称', '实际', '市值']]
            return actual_df[actual_df['实际'] != 0]
        except Exception as e:
            print(e)
            print(
                f'Error: {self.account}实际持仓数据获取失败，请检查{self.location_dict["actual"]}文件是否存在，两分钟后重试')
            time.sleep(120)
            self.get_actual_position()

    def get_position_col(self):
        # 普通账户目前有三种，分别是盼澜1号，踏浪1号，听涟2号
        account_col_dict = {
            '盼澜1号': {
                'actual code': '代码',
                'actual name': '名称',
                'actual': '当前余额',
                'actual market val': '参考市值',
                'actual account': '账户',
                'target code': '代码',
                'target': '目标',
            },
            '听涟2号': {
                'actual code': '证券代码',
                'actual name': '证券名称',
                'actual': '持仓数量',
                'actual market val': '市值',
            },
        }
        account_col_dict['踏浪1号'] = account_col_dict['盼澜1号']
        if self.account in account_col_dict.keys():
            return account_col_dict[self.account]
        else:
            raise ValueError(f'Error: account {self.account} is not supported')
