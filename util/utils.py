import time
import os
import glob
import datetime
import pandas as pd
import numpy as np

import multiprocessing as mul
from EmQuantAPI import c
from functools import wraps
import rqdatac as rq


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


def get_newest_file(directory, key):
    file_list = glob.glob(f'{directory}/*{key}*')
    if file_list == []:
        print(f'未找到{key}文件, retry in 2 mins')
        time.sleep(120)
        return get_newest_file(directory, key)

    time_list = [os.path.getmtime(file) for file in file_list]
    newest_file = file_list[time_list.index(max(time_list))]
    return newest_file


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


def find_index_loc_in_excel(file_path, sheet_name, value):
    """

    :param file_path:
    :param sheet_name:
    :param value:
    :return: the excel row number of the value in the sheet, if not found, return the next row number
    """
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


def check_file_gen_time(path_list, check_date=None, check_hour=None):
    check_hour = 15 if check_hour is None else check_hour
    check_date = pd.to_datetime(check_date).strftime('%Y%m%d') if check_date is not None else time.strftime('%Y%m%d')
    check_time = pd.to_datetime(check_date + ' ' + str(check_hour) + ':00:00')
    for path in path_list:
        gen_time = datetime.datetime.fromtimestamp(os.path.getmtime(path))
        if gen_time < check_time:
            return False
    return True


def add_df_cell(df, col_list, is_df=False):
    if isinstance(col_list, str):
        col_list = [col_list]
    if is_df:
        selected_col = [col for col in df.columns for p in col_list if p in col]
        return df[selected_col].sum(axis=1).sum()
    else:
        selected_col = [col for col in df.index for p in col_list if p in col]
        return df[selected_col].sum()


def gen_info_dict(df, key_list, col_list, is_df=False):
    info_dict = {
        key: add_df_cell(df, col, is_df=is_df) for key, col in list(zip(key_list, col_list))
    }
    return info_dict


def get_value(df, key, vertical=True):
    if vertical:
        return df.iloc[np.where(df.values == key)[0][0] + 1,
        np.where(df.values == key)[1][0]]
    else:
        return df.iloc[np.where(df.values == key)[0][0],
        np.where(df.values == key)[1][0] + 1]


def sep_df(start, end=None, df=None):
    df = df.reset_index(drop=False)
    loc_start = np.where(df.values == start)[0][0] + 1
    if end is not None:
        locs_end = sorted(np.where(df.values == end)[0])
        loc_end = [loc for loc in locs_end if loc > loc_start][0]
    else:
        loc_end = None
    new_df = df.iloc[loc_start:loc_end].dropna(axis=1, how='all')
    new_df.columns = new_df.iloc[0]
    return new_df.iloc[1:].dropna(how='any')


def get_instruments_type(df, col_name):
    stock = rq.all_instruments(type='CS')['order_book_id'].str.split('.', expand=True)[0].tolist()
    etf = rq.all_instruments(type='ETF')['order_book_id'].str.split('.', expand=True)[0].tolist()
    convertible = rq.all_instruments(type='Convertible')['order_book_id'].str.split('.', expand=True)[0].tolist()
    df['security type'] = df[col_name].apply(
        lambda x: 'CS' if x in stock else 'ETF' if x in etf else 'Convertible' if x in convertible else 'Other')
    return df
