#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/12/22 15:10
# @Author  : Suying
# @Site    : 
# @File    : med_kc_stock_pred.py
import os.path
import time

import pandas as pd
import rqdatac as rq
from util.file_location import FileLocation
from util.send_email import Mail, R

def send_med_stock_list(date=None):
    date = time.strftime('%Y%m%d') if date is None else date
    file_path = get_med_stock_list(date=date)
    if os.path.exists(file_path):
        subject = f'[CNN策略因子预测值]{date}'
        content = f"""
            <table width="800" border="0" cellspacing="0" cellpadding="4">
            <tr>
            <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>CNN策略因子预测值</b></td>
            </tr>
            <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
            <p><b>文件路径:</b></p>
            &nbsp&nbsp {file_path}
            <p><b>更新内容:</b></p>
            &nbsp&nbsp CNN各个子策略的因子预测值
            """

        attaches = [file_path]
        Mail().send(subject=subject, body_content=content, attachs=attaches, receivers=R.department['research'] + R.department['admin'])



def get_med_stock_list(date=None):
    date = time.strftime('%Y%m%d') if date is None else date
    file_dir = FileLocation.factor_dir
    path = rf'{file_dir}\cnn_pred_{date}.pkl'
    if os.path.exists(path):
        print(f'{path} exists')
        df = pd.read_pickle(path)
    else:
        print(f'{path} doesn\'t exist, please check if file is ready, retry in 5 mins')
        time.sleep(300)
        return get_med_stock_list(date=date)

    rq.init()
    stocks = df.index.tolist()
    formatted_stocks = [stock[2:] + '.' + stock[:2].upper() for stock in stocks]
    df.index = rq.id_convert(formatted_stocks)

    stock_info = rq.instruments(df.index.tolist())
    stock_info_df = pd.DataFrame(index=[stock.order_book_id for stock in stock_info],
                                 columns=['名称', '行业'])
    stock_info_df['名称'] = [stock.symbol for stock in stock_info]
    stock_info_df['行业'] = [stock.citics_industry_name for stock in stock_info]

    kc50_list = rq.id_convert(get_kc_50(date))
    stock_info_df['科创50成分股'] = '否'
    kc50_stocks = [stock for stock in kc50_list if stock in stock_info_df.index]
    stock_info_df.loc[kc50_stocks, '科创50成分股'] = '是'

    merged_df = pd.concat([stock_info_df, df], axis=1)
    merged_df = merged_df.sort_index()
    save_path = rf'\\192.168.1.116\kline\cnn_factor\{date}.csv'
    merged_df.to_csv(save_path, encoding='utf_8_sig')
    print(f'{save_path} is saved')
    return save_path


def get_kc_50(date):
    df = pd.read_csv(rf'{FileLocation.kc50_composition_dir}\{date}.csv')
    return df.iloc[:, 0].tolist()


if __name__ == '__main__':
    send_med_stock_list()
