import os
import time

import pandas as pd
import rqdatac as rq


def get_talang1_ret(date=None):
    date = pd.to_datetime(date).strftime('%Y%m%d') if date is not None else time.strftime('%Y%m%d')
    account_df = pd.read_excel(rf'C:\Users\Yz02\Desktop\strategy_update\cnn策略观察_{date}.xlsx', sheet_name='踏浪1号',
                               index_col=0)
    account_df.index = account_df.index.astype(str)
    talang1_ret = account_df.loc[date, '当日收益率']
    return talang1_ret


def get_kc50_stock_list(date=None):
    date = date if date is not None else time.strftime('%Y-%m-%d')
    rq.init()
    return rq.index_components('000688.XSHG', date=date)

def retry_get_kc50_ret(date=None):
    date = pd.to_datetime(date).strftime('%Y-%m-%d') if date is not None else time.strftime('%Y-%m-%d')
    def get_kc50_ret(date1):
        df = rq.get_price_change_rate('000688.XSHG', start_date=date1, end_date=date1)
        if df is None:
            print(f'No data for kc50 ret {date1}, retry in 10 seconds')
            time.sleep(10)
            get_kc50_ret(date1)
        else:
            return df.iloc[0, 0]
    return get_kc50_ret(date)

def get_kc_stock_pct(date=None):
    date = pd.to_datetime(date).strftime('%Y-%m-%d') if date is not None else time.strftime('%Y-%m-%d')
    kc_stock_s = get_kc_stock_info(date)['order_book_id']
    pct_s = rq.get_price_change_rate(kc_stock_s.tolist(), start_date=date, end_date=date).iloc[0]
    return pct_s


def get_kc_stock_info(date=None):
    date = date if date is not None else time.strftime('%Y-%m-%d')
    kc_stock_info_df = rq.all_instruments(type='CS', market='cn', date=date).query('board_type=="KSH"')
    return kc_stock_info_df

if __name__ == '__main__':

    print(retry_get_kc50_ret())