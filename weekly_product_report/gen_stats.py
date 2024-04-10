#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/10 13:43
# @Author  : Suying
# @Site    : 
# @File    : gen_stats.py


import pandas as pd
import rqdatac as rq

from util.trading_calendar import TradingCalendar as tc
from weekly_product_report.obtain_nav import db_connect, get_db_data


class ProductStats:
    def __init__(self):
        rq.init()
        self.index_code_dict = {
            '踏浪1号': '000688.SH',
            '踏浪2号': '000905.SH',
            '踏浪3号': '000852.SH',
        }
        self.table_name_dict = {
            '弄潮2号': 'nongchao2_weekly_value',
            '弄潮1号': 'nongchao_weekly_value',
            '踏浪1号': 'talang_weekly_value',
            '踏浪2号': 'talang2_weekly_value',
            '踏浪3号': 'talang3_weekly_value',
            '听涟2号': 'tinglian2_weekly_value',
            '盼澜1号': 'panlan_weekly_value',
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

    def get_all_stats(self, start_date, end_date):
        nav_dict = self.get_nav_history()

        check_end = {key: pd.to_datetime(end_date) in nav_dict[key].index for key in nav_dict.keys()}
        check_start = {key: pd.to_datetime(start_date) in nav_dict[key].index for key in nav_dict.keys()}
        available_product = [key for key in check_end.keys() if check_end[key] and check_start[key]]

        if all([value for value in check_end.values()]) and all([value for value in check_start.values()]):
            print('净值数据完整，开始计算业绩')
        else:
            print(end_date, check_end)
            print(start_date, check_start)
            print(start_date, end_date, '净值数据不完整，请检查数据库')

        reset_nav_dict = self.set_daily_date(nav_dict)
        stats = {k: self.get_statistics(
            key=k,
            nav_s=reset_nav_dict[k],
            start_date=start_date,
            end_date=end_date,
        ) for k in available_product}
        return stats

    def get_nav_history(self):
        connection = db_connect()
        nav_dict = {k: get_db_data(connection, v)
                    for k, v in self.table_name_dict.items()}
        return nav_dict

    def set_daily_date(self, nav_dict):
        reset_nav_dict = {}
        for key in nav_dict.keys():
            reset_nav_dict[key] = self.select_trading_days(nav_dict, key)
            print(key, '净值初始时间重置成功', '初始时间为', self.start_date[key].strftime('%Y%m%d'))
        return reset_nav_dict

    def select_trading_days(self, nav_dict, key):
        nav_s = nav_dict[key].loc[self.start_date[key]:, 'cumu_netvalue2']
        weeks = pd.Series([date.strftime('%Y%W') for date in nav_s.index], index=nav_s.index, name='week')
        weekdays = pd.Series([int(date.strftime('%w')) for date in nav_s.index], index=nav_s.index, name='weekday')
        calendar = pd.concat([weeks, weekdays], axis=1)
        calendar = calendar.query('(weekday > 0)&(weekday < 6)')

        last_trade_day_of_week = calendar.groupby(['week']).tail(1).index
        if pd.to_datetime(self.start_date[key]) not in last_trade_day_of_week:
            last_trade_day_of_week = last_trade_day_of_week.insert(0, pd.to_datetime(self.start_date[key]))
        return nav_s.loc[last_trade_day_of_week]

    def get_statistics(self, nav_s, key, start_date, end_date):
        end = pd.to_datetime(end_date)
        start = pd.to_datetime(start_date)
        week_num = tc().calculate_trading_weeks(start=nav_s.index[0], end=end) - 1
        print(key, '周数为', week_num, '周', '开始时间为', nav_s.index[0], '结束时间为', end)

        statistics = {
            '累计净值': nav_s.loc[end],
            '当周收益': nav_s.loc[end] / nav_s.loc[start] - 1,
            '历史最大回撤': self.get_mdd(nav_s.loc[:end]),
        }
        statistics['年化收益'] = (nav_s.loc[end] / nav_s.iloc[0]) ** (52 / week_num) - 1

        if key in self.index_code_dict.keys():
            index_nav_s = self.get_index_ret(
                index_code=self.index_code_dict[key],
                start=nav_s.index[0].strftime('%Y%m%d'),
                end=end.strftime('%Y%m%d'),
            )

            common_index = index_nav_s.index.intersection(nav_s.index)
            assert end in common_index
            assert start in common_index
            index_nav_s = index_nav_s.loc[common_index]
            nav_s = nav_s.loc[common_index]

            excess_nav = nav_s / index_nav_s
            statistics.update({
                '当周超额': excess_nav.loc[end] / excess_nav.loc[start] - 1,
                '超额最大回撤': self.get_mdd(excess_nav),
                '年化超额': (excess_nav.loc[end] / excess_nav.iloc[0]) ** (52 / week_num) - 1,
            })

        return statistics

    def get_index_ret(self, index_code, start, end):
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

