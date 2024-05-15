#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/5/15 9:14
# @Author  : Suying
# @Site    : 
# @File    : download_beta.py
import os
import pandas as pd
import numpy as np
import rqdatac as rq
import glob
import h5py

def get_beta(window=120):
    # rq.init()
    # index = rq.get_price_change_rate('000905.XSHG', start_date='2018-01-01', end_date='2024-05-14')
    # index.to_pickle('zz500_ret.pkl')
    index_path = r'kc50_ret.pkl'
    index_code = '000688.XSHG'
    suffix = 'kc50'
    index_s = pd.read_pickle(index_path)
    path = r'D:\data\adjusted_kline19_24_kc.pkl'
    df = pd.read_pickle(path)['pct_chg'].swaplevel().sort_index()

    beta_data = []

    for stock in df.index.levels[0]:
        stock_df = df.loc[stock].rename(stock)
        new_df = pd.merge(stock_df, index_s, left_index=True, right_index=True, how='left').dropna()

        beta = new_df.apply(
            lambda row: custom_rolling_cov(new_df[stock].loc[:row.name], new_df[index_code].loc[:row.name], window),
            axis=1)
        beta = beta.dropna().rename(stock)
        beta_data.append(beta)
        print(stock, 'done', len(beta), 'days')

    beta_df = pd.concat(beta_data, axis=1)
    beta_df = beta_df[beta_df.index > pd.to_datetime('20200101')]
    beta_s = beta_df.stack().rename('beta')


    beta_s.to_pickle(f'{suffix}_beta{window}.pkl')


def custom_rolling_cov(x, y, window):
    if len(x) == 1:
        return np.nan
    elif len(x) < window:
        cov = np.cov(x, y)[0, 1]
        var = np.var(y)
    else:
        cov = np.cov(x[-window:], y[-window:])[0, 1]
        var = np.var(y[-window:])
    beta = cov / var
    return beta


if __name__ == '__main__':
    rq.init()
    save_dir = r'D:\data\archive\index'
    index_info = pd.read_csv(rf'{save_dir}\index_info.csv', index_col=0)



    file_lst = glob.glob(rf'{save_dir}\raw\*.pkl')
    h5_file = rf'{save_dir}\index20240514.h5'

    with h5py.File(h5_file, 'r') as f:
        keys = f.keys()







    with h5py.File(rf'{save_dir}\index.h5', 'w') as f:
        for file in file_lst:
            index_code = os.path.basename(file)[:-4]
            symbol = index_info.loc[index_code, 'symbol']
            index_price = pd.read_pickle(file)
            f.create_dataset(index_code, data=index_price)
            print(index_code, 'done')








    # for index_code in index_info.index:
    #     try:
    #         symbol = index_info.loc[index_code, 'symbol']
    #         index_price = rq.get_price(index_code, start_date='19900101', end_date='2024-05-14')
    #         index_price = index_price.droplevel(0)
    #         index_price['pct_chg'] = index_price['close']/index_price['prev_close'] - 1
    #         index_price.to_pickle(rf'{save_dir}\raw\{index_code}.pkl')
    #         print(index_code+symbol, 'done')
    #     except Exception as e:
    #         print(index_code, e)


