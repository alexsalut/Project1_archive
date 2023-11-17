#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/1 15:34
# @Author  : Suying
# @Site    : 
# @File    : factor_quantile_eval.py

import time

import pandas as pd
import rqdatac as rq

from util.file_location import FileLocation as FL
from util.utils import transfer_to_jy_ticker


class FactorQuantileEval:
    def __init__(self, date=None):
        self.date = pd.to_datetime(date).strftime("%Y%m%d") if date is not None else time.strftime('%Y%m%d')
        self.file_path = self.get_file_path(self.date)
        print('File path:', self.file_path)

    def get_all_group_ret_rank(self):
        data = []
        for factor in ['I10R5', 'I10R2', 'I5R2']:
            data.append(self.get_group_ret(factor))
        group_ret = pd.concat(data, axis=1)
        group_rank = group_ret.rank(axis=0, ascending=True)

        ret_text = group_ret.to_html(float_format='%.2f')

        rank_text = group_rank.to_html(float_format='%.0f')

        return ret_text, rank_text

    def get_group_ret(self, factor):
        group_s = self.get_factor_group(factor)
        group_num = len(group_s.unique())

        ret_df = pd.read_csv(self.file_path['raw daily bar'], index_col=0)
        ret_df.index = transfer_to_jy_ticker(ret_df.index)

        group_ret_s = pd.Series(index=['CNN' + str(group_num - i) for i in range(group_num)], name=factor)
        for i in range(group_num):
            stock_list = group_s[group_s == i].index.tolist()
            group_ret_s[f'CNN{i + 1}'] = ret_df.loc[stock_list, 'pct_chg'].mean()
        return group_ret_s

# group stocks by factor into 5 groups in an ascending order
    def get_factor_group(self, factor):
        factor_path = self.file_path[factor]
        factor_s = pd.read_pickle(factor_path)
        group_s = pd.qcut(factor_s, 5, labels=False)
        return group_s

    def get_file_path(self, date):
        rq.init()
        last_trade_date = pd.to_datetime(rq.get_previous_trading_date(date, 1)).strftime('%Y%m%d')
        dict = {
            factor: rf'{FL().factor_dir}/cnn_pred_{factor}_{last_trade_date}.pkl' for factor in ['I10R5', 'I10R2', 'I5R2']
        }
        dict.update({'raw daily bar': rf'{FL.raw_daily_dir}/{date[:4]}/{date[:6]}/raw_daily_{date}.csv' })
        return dict


if __name__ == '__main__':
    f = FactorQuantileEval('20231031')
    print(f.get_all_group_ret_rank())
