#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/10 10:35
# @Author  : Suying
# @Site    : 
# @File    : obtain_nav.py
import pandas as pd
import mysql.connector

def db_connect():
    connection = mysql.connector.connect(host='120.24.4.184',
                                         database='yanzhou_netvalue',
                                         user='yanzhou',
                                         password='Yanzhou@1117.')
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


    df = get_db_data(db_connect(), 'nongchao2_daily_value')
    print()


