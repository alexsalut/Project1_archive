#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/10 13:43
# @Author  : Suying
# @Site    : 
# @File    : gen_stats.py
from datetime import datetime, timedelta

import pandas as pd

from weekly_product_report.obtain_nav import get_product_nav
import rqdatac as rq


class ProductStats:
    def __init__(self, end):
        self.end = pd.to_datetime(end)
        self.start = self.end - timedelta(days=7)
        self.index_code_dict = {
            '踏浪2号': '000905.SH',
            '踏浪3号': '000852.SH',
            '踏浪1号': '000688.SH'
        }
        self.table_name_dict = {
            '弄潮2号': 'nongchao2_daily_value',
            '弄潮1号': 'nongchao_daily_value',
            '踏浪1号': 'talang_daily_value',
            '踏浪2号': 'talang2_daily_value',
            '踏浪3号': 'talang3_daily_value',
            '听涟2号': 'tinglian2_daily_value',
            '盼澜1号': 'panlan_daily_value',
        }
        self.start_date = {
            '弄潮1号': pd.to_datetime('20230303'),
            '弄潮2号': pd.to_datetime('20230303'),
            '踏浪1号': pd.to_datetime('20230928'),
            '踏浪2号': pd.to_datetime('20230728'),
            '踏浪3号': pd.to_datetime('20230602'),
            '听涟2号': pd.to_datetime('20230407'),
            '盼澜1号': pd.to_datetime('20220909'),

        }

    def get_all_stats(self):
        nav_dict = get_product_nav(self.table_name_dict)
        reset_nav_dict = self.set_weekly_date(nav_dict)
        stats = {}
        for key in reset_nav_dict.keys():
            stats[key] = self.get_statistics(nav_s=reset_nav_dict[key], key=key)

        return stats

    def set_weekly_date(self, nav_dict):
        reset_nav_dict = {}
        for key in nav_dict.keys():
            reset_nav_dict[key] = nav_dict[key].loc[self.start_date[key]:, 'cumu_netvalue']
            reset_nav_dict[key] = self.select_fridays(reset_nav_dict[key], key)
            reset_nav_dict[key] /= reset_nav_dict[key].iloc[0]
            print(key, '净值初始时间重置成功', '初始时间为', self.start_date[key].strftime('%Y%m%d'))
        return reset_nav_dict

    def select_fridays(self, nav_s, key):
        fridays = [date for date in nav_s.index if date.weekday() == 4]
        if self.start_date[key] not in fridays:
            fridays.append(self.start_date[key])
        return nav_s.loc[fridays].sort_index()

    def get_statistics(self, nav_s, key):
        statistics = {
            '累计净值': nav_s.iloc[-1],
            '当周收益': nav_s.loc[self.end] / nav_s.loc[self.start] - 1,
            '历史最大回撤': self.get_mdd(nav_s),
        }
        statistics.update({'年化收益': (nav_s.iloc[-1])**(52/(len(nav_s)-1)) - 1})

        if key in self.index_code_dict.keys():
            index_nav_s = self.get_index_ret(self.index_code_dict[key], nav_s.index[0].strftime('%Y%m%d'),
                                             self.end.strftime('%Y%m%d')).loc[nav_s.index]
            excess_nav = nav_s / index_nav_s
            statistics.update({
                '当周超额': excess_nav.loc[self.end] / excess_nav.loc[self.start] - 1,
                '超额最大回撤': self.get_mdd(excess_nav),
                '年化超额': (excess_nav.iloc[-1])**(52/(len(excess_nav)-1)) - 1,
            })

        return statistics

    def get_index_ret(self, index_code, start, end):
        rq.init()
        order_book_ids = rq.id_convert(index_code)
        index_ret = rq.get_price_change_rate(
            order_book_ids,
            start_date=start,
            end_date=end).iloc[:, 0]
        index_nav = (index_ret + 1).cumprod()
        index_nav /= index_nav.iloc[0]
        return index_nav

    def get_mdd(self, nav):
        mdd = (nav / nav.cummax() - 1).min()
        return mdd


if __name__ == '__main__':
    ProductStats('20231103').get_all_stats()
