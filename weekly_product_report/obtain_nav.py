#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/10 10:35
# @Author  : Suying
# @Site    : 
# @File    : obtain_nav.py

import mysql.connector
import pandas as pd
from datetime import datetime, timedelta


def get_product_nav(table_name_dict):
    nav_dict = {}

    for key in table_name_dict.keys():
        nav_dict[key] = get_db_data(table_name_dict[key])
        print(key, '净值获取成功')
    return nav_dict


def get_db_data(table_name):
    connection = db_connect()
    select_query = f"SELECT * FROM {table_name}"
    cursor = connection.cursor()
    cursor.execute(select_query)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(rows, columns=columns).set_index('date', drop=True)
    df.index = pd.to_datetime(df.index)
    return df


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



