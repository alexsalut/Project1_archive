# -*- coding: utf-8 -*-
# @Time    : 2022/12/6 15:48
# @Author  : Youwei Wu
# @File    : fq_kline.py
# @Software: PyCharm

"""
本脚本用于生成图像识别模型的回测数据，
训练数据区间为2000-2016年，
测试数据区间为2017-至今。
"""

import glob

import pandas as pd

from util.utils import transfer_to_jy_ticker


class FqKLine:

    def __init__(self,
                 tushare_dir,
                 save_path,
                 ):
        self.tushare_dir = tushare_dir
        self.save_path = save_path

    def gen_qfq_kline(self):
        ts_kline_df = self.collect_daily_bar()
        raw_kline_df = self.fix_tushare_df_format(ts_kline_df)

        qfq_price = raw_kline_df.groupby('ticker').apply(self.backward_fq)
        qfq_price = qfq_price.reset_index(0, drop=True).swaplevel().sort_index()
        qfq_price.to_pickle(self.save_path)
        self.extract_price_of_kc_stocks()

    def collect_daily_bar(self):
        data = []
        locs = glob.glob(rf'{self.tushare_dir}\2023\*\*.csv')
        for loc in locs:
            print(loc)
            tushare_df = pd.read_csv(loc, converters={'trade_date': str})
            del tushare_df['change']
            del tushare_df['pct_chg']
            data.append(tushare_df)

        ts_kline_df = pd.concat(data)
        return ts_kline_df

    @staticmethod
    def fix_tushare_df_format(ts_kline_df):
        """
        Parameters
        -------
        ts_kline_df: pd.DataFrame
            名称	        类型	    描述
            ts_code	    str	    股票代码
            trade_date	str	    交易日期
            open	    float	开盘价
            high	    float	最高价
            low	        float	最低价
            close	    float	收盘价
            pre_close	float	昨收价(前复权)
            vol	        float	成交量 （手）
            amount	    float	成交额 （千元）
        """

        kline_df = ts_kline_df.rename(columns={
            'ts_code': 'ticker',
            'trade_date': 'date',
            'vol': 'volume',
        })
        kline_df['date'] = pd.to_datetime(kline_df['date'])
        kline_df['ticker'] = transfer_to_jy_ticker(kline_df['ticker'])
        kline_df = kline_df.set_index(['ticker', 'date']).sort_index()
        kline_df['pct_chg'] = kline_df['close'] / kline_df['pre_close'] - 1
        del kline_df['pre_close']
        return kline_df

    @staticmethod
    def backward_fq(raw_price):
        real_ret = raw_price['pct_chg']
        real_ret.iat[0] = 0
        real_nav = (real_ret + 1).cumprod()
        real_nav /= real_nav.iat[-1]
        assert real_nav.iat[-1] == 1

        raw_ret = raw_price['close'].pct_change().fillna(0)
        raw_nav = (raw_ret + 1).cumprod()
        raw_nav /= raw_nav.iat[-1]

        multiplier = real_nav / raw_nav

        fq_price = raw_price.copy()
        fq_price[['open', 'high', 'low', 'close']] = \
            fq_price[['open', 'high', 'low', 'close']].mul(multiplier, axis=0)

        fq_price['ma5'] = fq_price['close'].rolling(5).mean()  # 此步也不可修改
        return fq_price.dropna()  # 此步至关重要，万万不可修改

    def extract_price_of_kc_stocks(self):

        price = pd.read_pickle(self.save_path)

        all_stocks = price.index.levels[1]
        kc_stocks = all_stocks[all_stocks.str.startswith('sh68')]

        kc_price_list = [price.xs(x, level=1) for x in kc_stocks]
        kc_price_df = pd.concat(kc_price_list, keys=kc_stocks).swaplevel().sort_index()
        kc_price_df.to_pickle(self.save_path.replace('.pkl', '_kc.pkl'))
