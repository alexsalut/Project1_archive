#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/10 13:43
# @Author  : Suying
# @Site    : 
# @File    : gen_stats.py

import mysql.connector

import pandas as pd
import rqdatac as rq

from datetime import timedelta


class ProductStats:
    def __init__(self):
        self.index_code_dict = {
            '踏浪1号': '000688.SH',
            '踏浪2号': '000905.SH',
            '踏浪3号': '000852.SH',
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

    def get_all_stats(self, end_date):
        connection = db_connect()
        nav_dict = {k: get_db_data(connection, v)
                    for k, v in self.table_name_dict.items()}
        reset_nav_dict = self.set_weekly_date(nav_dict)
        stats = {k: self.get_statistics(
            key=k,
            nav_s=v,
            end_date=end_date,
        ) for k, v in reset_nav_dict.items()}
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

    def get_statistics(self, nav_s, key, end_date):
        end = pd.to_datetime(end_date)
        start = end - timedelta(days=7)
        statistics = {
            '累计净值': nav_s.iloc[-1],
            '当周收益': nav_s.loc[end] / nav_s.loc[start] - 1,
            '历史最大回撤': self.get_mdd(nav_s),
        }
        statistics.update({'年化收益': (nav_s.iloc[-1])**(52/(len(nav_s)-1)) - 1})

        if key in self.index_code_dict.keys():
            index_nav_s = self.get_index_ret(
                index_code=self.index_code_dict[key],
                start=nav_s.index[0].strftime('%Y%m%d'),
                end=end.strftime('%Y%m%d'),
            ).loc[nav_s.index]
            excess_nav = nav_s / index_nav_s
            statistics.update({
                '当周超额': excess_nav.loc[end] / excess_nav.loc[start] - 1,
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


def db_connect():
    connection = mysql.connector.connect(host='39.98.41.75',
                                         database='yanzhou_netvalue',
                                         user='yanzhou',
                                         password='yanzhou0801')
    if connection.is_connected():
        print('数据库连接成功')
        return connection
    else:
        print('数据库连接失败')
        return db_connect()


def get_db_data(connection, table_name):
    select_query = f"SELECT * FROM {table_name}"
    cursor = connection.cursor()
    cursor.execute(select_query)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(rows, columns=columns).set_index('date', drop=True)
    df.index = pd.to_datetime(df.index)
    print(table_name, '净值获取成功')
    return df


if __name__ == '__main__':
    ProductStats().get_all_stats(end_date='20231111')
