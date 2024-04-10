import smtplib
import time
import os

import pandas as pd
import numpy as np

import multiprocessing as mul
from email.mime.text import MIMEText
from EmQuantAPI import c
from functools import wraps
import matplotlib.pyplot as plt


def c_get_trade_dates(start, end):
    c.start("ForceLogin=1")
    c_data = c.tradedates(start, end, "period=1").Data
    trade_dates = pd.to_datetime(c_data).strftime('%Y%m%d')
    c.stop()
    return list(trade_dates)


def transfer_to_jy_ticker(universe, inverse=False):
    """
    input: [601919.SH, 000333.SZ]
    output: [sh601919, sz000333]
    """
    if inverse:
        return [x[-6:] + '.' + x[:2].upper() for x in universe]
    else:
        return [x.split('.')[-1].lower() + x.split('.')[0] for x in universe]


def fill_in_stock_code(stock_list):
    stock_list = [x + '.SH' if x[:1] == '6' else x + '.SZ' for x in stock_list]
    return stock_list


def add_data_label(period_return):
    for i, x in enumerate(period_return):
        drift = .001 if x >= 0 else -.006
        color = 'red' if x > 0 else 'green'
        plt.text(i - .5, x + drift, f'{round(x * 100, 1)}%', color=color, fontdict={'family': 'Microsoft YaHei'})


def retry_save_excel(wb, file_path):
    try:
        wb.save(file_path)
        print(f'File has been saved: {file_path}')
    # Which exception ???
    except Exception as e:
        print(e)
        print(f'File cannot be saved, wait for 10 seconds: {file_path}')
        time.sleep(10)
        retry_save_excel(wb, file_path)


def retry_remove_excel(file_path):
    try:
        os.remove(file_path)
        print(f'{file_path} has been removed')
    except Exception as e:
        print(e)
        print(f'{file_path} cannot be removed, wait for 10 seconds')
        time.sleep(10)
        retry_remove_excel(file_path)


def multi_task(func, tasks, n_cpu=10):
    pool = mul.Pool(processes=n_cpu)
    pool_result = [pool.apply_async(func, args=(task,))
                   for task in tasks]
    data = [r.get() for r in pool_result]
    return data


class SendEmailInfo:
    department = {
        'research': ['zhou.sy@yz-fund.com.cn', 'wu.yw@yz-fund.com.cn'],
        'tech': ['liu.ch@yz-fund.com.cn', 'ling.sh@yz-fund.com.cn'],
        'admin': ['chen.zf@yz-fund.com.cn']
    }


def find_index_loc_in_excel(file_path, sheet_name, value):
    df = pd.read_excel(file_path, sheet_name=sheet_name, index_col=False, header=None)
    df = df.dropna(axis=1, how='all')
    df[0] = df[0].astype(str).str.split('.').str[0]
    loc = np.where(df[0].values == value)
    if loc[0].size == 0:
        return len(df) + 1
    else:
        return loc[0][0] + 1



def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        print(f'  {func.__name__} 执行时间：{end_time - start_time:.8f}s')
        return result
    return wrapper