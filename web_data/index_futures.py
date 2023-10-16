# -*- coding: utf-8 -*-
# @Time    : 2023/9/18 8:42
# @Author  : Youwei Wu
# @File    : index_futures.py
# @Software: PyCharm

import os
import glob
import time
import zipfile
import rarfile
import requests

import pandas as pd

from file_location import FileLocation as FL

def update_daily_futures(
        month=None
):
    cffe_dir = FL().future_dir
    obj = CffeFutures(cffe_dir=cffe_dir)

    if month is None:
        today = time.strftime("%Y%m%d")
        mark_date = pd.bdate_range(end=today, periods=5)[0].strftime("%Y%m%d")
        obj.scrape_data(month=today[:6])
        if mark_date[:6] != today[:6]:
            obj.scrape_data(month=mark_date[:6])
    else:
        obj.scrape_data(month=month)

    gen_index_futures_data(cffe_dir=cffe_dir)


class CffeFutures:
    def __init__(
            self,
            cffe_dir,
    ):
        self.decompress_root = f'{cffe_dir}/datasrc'
        self.zip_dir = f'{cffe_dir}/zip_files'

    # def download_history(self):
    #     for year in range(2016, 2022):
    #         for m in range(1, 13):
    #             sep = '0' * (2 - len(str(m)))
    #             self.scrape_data(month=f'{year}{sep}{m}')

    def update_cffex_data(self, date=None):
        date = time.strftime('%Y%m%d') if date is None else date
        self.scrape_data(month=date[:6])
        self.gen_settle_price('IC')

    def scrape_data(self, month):
        try:
            url = f'http://cffex.com.cn/sj/historysj/{month}/zip/{month}.zip'
            zip_loc = f'{self.zip_dir}/{month}.zip'
            cache_path = os.path.join(self.decompress_root, month[:4], month)
            os.makedirs(cache_path, exist_ok=True)

            print('download cffe data of', month)
            self.get_file_from_link(url, zip_loc)
            decompress(zip_loc, decompress_to=cache_path)

        except zipfile.BadZipfile:
            time.sleep(300)
            self.scrape_data(month)

    @staticmethod
    def get_file_from_link(url, save_loc):
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        }
        data = requests.get(url, headers=headers)
        with open(save_loc, 'wb') as f:
            f.write(data.content)

    def gen_settle_price(self, ticker='IC'):
        files = sorted(os.listdir(self.decompress_root))
        ic_df = pd.DataFrame()
        for fn in files:
            print('get', fn)
            daily_df = self.get_daily_df(fn)
            daily_ic_df = daily_df[daily_df['ticker'].str.contains(ticker)]
            ic_df = pd.concat([ic_df, daily_ic_df])
        ic_df['date'] = pd.to_datetime(ic_df['date'])
        ic_df['ticker'] = ic_df['ticker'].str.strip()
        ic_df = ic_df.set_index(['date', 'ticker']).sort_index()
        ic_df['pre_close'] = ic_df['close'].groupby('ticker').shift(1)
        settle_price = f'/data/data/cffe/{ticker}_settle_price.pkl'
        ic_df.to_pickle(settle_price)

    def get_daily_df(self, fn):
        date = fn.split('_')[0]
        loc = os.path.join(self.decompress_root, fn)
        df = pd.read_csv(loc, encoding='gbk')
        daily_df = df[['合约代码', '今开盘', '今收盘', '成交量', '今结算', '前结算']]
        daily_df.columns = ['ticker', 'open', 'close', 'volume', 'settle', 'pre_settle']
        daily_df['date'] = date
        return daily_df


def gen_index_futures_data(cffe_dir):
    all_files = glob.glob(f'{cffe_dir}/datasrc/*/*/*.csv')
    all_data = []
    for loc in all_files:
        print(loc)
        df = pd.read_csv(loc, encoding='gbk')
        tmp_df = df[~df['合约代码'].isin(['小计', '合计'])].copy()
        tmp_df = tmp_df.rename(columns={
            '合约代码': 'ticker',
            '今开盘': 'open',
            '最高价': 'high',
            '最低价': 'low',
            '成交量': 'volume',
            '成交金额': 'amount',
            '持仓量': 'open_interest',
            '今收盘': 'close',
            '今结算': 'settle',
            '前结算': 'pre_settle',
        })
        tmp_df['ticker'] = tmp_df['ticker'].str.strip()
        tmp_df = tmp_df.loc[tmp_df['ticker'].str.startswith('I'), [
            'ticker', 'open', 'high', 'low', 'volume', 'amount',
            'open_interest', 'close', 'settle', 'pre_settle']
        ]
        tmp_df['date'] = pd.to_datetime(os.path.basename(loc).split('_')[0])
        tmp_df = tmp_df.set_index(['date', 'ticker'])
        all_data.append(tmp_df)
    all_df = pd.concat(all_data)

    close_df = all_df['close'].unstack()
    all_df['pre_close'] = close_df.shift(1).stack()
    all_df.to_pickle(f'{cffe_dir}/data/index_futures.pkl')


def decompress(src_loc, decompress_to=None):
    assert src_loc[-3:] in ['rar', 'zip']
    if decompress_to is None:
        decompress_to = os.path.dirname(src_loc)
    os.makedirs(decompress_to, exist_ok=True)
    print('decompress from: {}\n  decompress to: {}'.format(
        src_loc, decompress_to))
    if src_loc[-3:] == 'rar':
        rar = rarfile.RarFile(src_loc)
        rar.extractall(decompress_to)
    else:
        with zipfile.ZipFile(src_loc) as zf:
            zf.extractall(decompress_to)


if __name__ == '__main__':
    update_daily_futures()
