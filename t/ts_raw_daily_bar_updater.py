# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 9:03
# @Author  : Youwei Wu, Suying Zhou
# @File    : daily_update.py
# @Software: PyCharm

import os
import time
import rqdatac

import pandas as pd
import tushare as ts

from util.file_location import FileLocation as FL
from util.send_email import Mail, R
from util.utils import c_get_trade_dates


class RawDailyBarUpdater:
    def __init__(self):
        self.save_dir = FL().raw_daily_dir

    def update_and_confirm_raw_daily_bar(self, today=None):
        today = time.strftime('%Y%m%d') if today is None else today
        self.ts_download_raw_daily_bar_history(
            start_date='20220630',
            end_date=today,
        )
        tushare_path = rf'{self.save_dir}/{today[:4]}/{today[:6]}/raw_daily_{today}.csv'
        self.retry_download_check(tushare_path=tushare_path, date=today)

    def ts_download_raw_daily_bar_history(self, start_date, end_date):
        trade_dates = c_get_trade_dates(start_date, end_date)
        ts.set_token('7885a1002f5bbf605e1e5165aa56d4fcdd73325b2b94b4b863da9991')

        for date in trade_dates:
            cache_dir = rf'{self.save_dir}/{date[:4]}/{date[:6]}'
            os.makedirs(cache_dir, exist_ok=True)
            save_path = os.path.join(cache_dir, f'raw_daily_{date}.csv')

            if os.path.exists(save_path):
                print(save_path, 'has existed.')
            else:
                self.ts_download_raw_daily_bar(save_path, date)

    def ts_download_raw_daily_bar(self, save_path, date):
        """
        Returns
        -------
        daily_bar: pd.DataFrame

            名称	类型	描述
            ts_code	str	股票代码
            trade_date	str	交易日期
            open	float	开盘价
            high    float	最高价
            low     float	最低价
            close	float	收盘价
            pre_close	float	昨收价(前复权)
            change	float	涨跌额
            pct_chg	float	涨跌幅
            vol	    float	成交量 （手）
            amount	float	成交额 （千元）
        """
        pro = ts.pro_api()
        raw_daily_bar = pro.daily(trade_date=date).set_index('ts_code')
        raw_daily_bar = raw_daily_bar.loc[raw_daily_bar.index.str[-2:] != 'BJ']
        raw_daily_bar.to_csv(save_path)
        print(save_path, 'has downloaded.')

    def retry_download_check(self, tushare_path, date):
        check_raw_daily_bar_info = self.check_daily_info(tushare_path=tushare_path, date=date)
        if len(check_raw_daily_bar_info['missed_unsuspended_stock_list']):
            print(f"Missed stock list is not empty, "
                  f"missed stocks are {check_raw_daily_bar_info['missed_stock_list']}. "
                  f"Retry downloading {date}")
            os.remove(tushare_path)
            content = f"""
            <table width="800" border="0" cellspacing="0" cellpadding="4">
            <tr>
            <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>Raw Daily Bar with missing stocks</b></td>
            </tr>
            <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
            <p>Missed stocks are {check_raw_daily_bar_info['missed_stock_list']}</p>
            <p>Missed unsuspended stocks are {check_raw_daily_bar_info['missed_unsuspended_stock_list']}</p>
            <p>Retry downloading {date}</p>
            
            """
            Mail().send(
                subject='[Alert!!Raw Daily Bar] Unsuspended stock missed',
                body_content=content,
                receivers=[R.department['research'][0]]
            )

            time.sleep(300)
            self.update_and_confirm_raw_daily_bar(today=date)
        else:
            self.notify_with_email(info_dict=check_raw_daily_bar_info)

    def notify_with_email(self, info_dict):
        subject = '[Tushare Daily Bar] Data downloaded successfully'
        content = f"""
        <table width="800" border="0" cellspacing="0" cellpadding="4">
        <tr>
        <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>Raw Daily Bar Info</b></td>
        </tr>
        <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
        Latest raw daily bar info is as follows:
        
        <p>Download path: </p>
        &nbsp&nbsp{info_dict['tushare_path']}
        <p>Number of TuShare stocks(a, kc): </p>
        &nbsp&nbsp({info_dict['tushare_stock_count']}, {info_dict['tushare_kc_stock_count']})
        <p>Number of RiceQuant stocks(a, kc): </p>
        &nbsp&nbsp({info_dict['rice_quant_stock_count']}, {info_dict['rice_quant_kc_stock_count']})
        <p>Missed stock list: </p>
        &nbsp&nbsp{info_dict['missed_stock_list']}
        <p>Missed KC stock list: </p>
        &nbsp&nbsp{info_dict['missed_kc_stock_list']}
        <p>NA stocks: </p>
        &nbsp&nbsp{info_dict['na_stock_list']}

        """
        Mail().send(subject=subject, body_content=content, receivers=R.department['research'])

    def check_daily_info(self, tushare_path, date):
        tushare_df = pd.read_csv(tushare_path)
        rqdatac.init()
        ricequant_df = rqdatac.all_instruments(type='CS', market='cn', date=date)
        a_num, tushare_missed_a_stock_s = self.crosscheck_with_ricequant(ricequant_df=ricequant_df,
                                                                         tushare_df=tushare_df, date=date)
        kc_df = tushare_df[tushare_df['ts_code'].str.startswith('68')]
        kc_num, tushare_missed_kc_stock_s = self.crosscheck_with_ricequant(
            ricequant_df=ricequant_df,
            tushare_df=kc_df,
            board_type='KSH',
            date=date)

        check_dict = {
            'date': date,
            'tushare_path': tushare_path,
            'tushare_stock_count': len(tushare_df),
            'rice_quant_stock_count': a_num,
            'missed_stock_list': tushare_missed_a_stock_s.index.tolist(),
            'na_stock_list': tushare_df[tushare_df.isna().any(axis=1)].index.tolist(),
            'missed_unsuspended_stock_list': tushare_missed_a_stock_s[~tushare_missed_a_stock_s].index.tolist(),
            'tushare_kc_stock_count': len(kc_df),
            'rice_quant_kc_stock_count': kc_num,
            'missed_kc_stock_list': tushare_missed_kc_stock_s.index.tolist(),
            'missed_unsuspended_kc_stock_list': tushare_missed_kc_stock_s[~tushare_missed_kc_stock_s].index.tolist(),
        }
        return check_dict

    def crosscheck_with_ricequant(self, ricequant_df, tushare_df, date, board_type=None):
        if board_type == 'KSH':
            ricequant_stock_df = ricequant_df.query("board_type == 'KSH'")
        else:
            ricequant_stock_df = ricequant_df.copy()

        ricequant_stock_df.index = ricequant_stock_df['order_book_id'].str[:6]
        tushare_df.index = tushare_df['ts_code'].str[:6]
        tushare_missed_stock = ricequant_stock_df.index.difference(tushare_df.index)
        tushare_missed_stock_list = ricequant_stock_df.loc[tushare_missed_stock, 'order_book_id'].tolist()

        if tushare_missed_stock_list:
            tushare_missed_stock_s = rqdatac.is_suspended(tushare_missed_stock_list, date, date).loc[date]
        else:
            tushare_missed_stock_s = pd.Series()
        return len(ricequant_stock_df), tushare_missed_stock_s


if __name__ == '__main__':
    RawDailyBarUpdater().update_and_confirm_raw_daily_bar(today='20230912')
