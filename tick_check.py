#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/6 16:59
# @Author  : Suying
# @Site    : 
# @File    : tick_check.py


import os
import time
import glob

import numpy as np
import pandas as pd

from util.send_email import Mail, R
from util.utils import multi_task
from EmQuantAPI import c


class Tick:
    def __init__(self, date=None):
        self.tick_dir = r'\\192.168.1.251\h\data\RiceQuant\stock\ticks'
        self.record_path = r'check_results.txt'
        self.date = date if date is not None else time.strftime('%Y%m%d')
        self.daily_dir = rf'{self.tick_dir}/{self.date[:4]}/{self.date[:6]}/{self.date}'
        self.file_list = glob.glob(rf'{self.daily_dir}/*.h5')

    def check_daily(self):
        if os.path.exists(rf'\\192.168.1.251\h\signal\stock_ticks_{self.date}'):
            check_result = self.multi_task_daily()
            self.notify_with_email(check_result)
        else:
            Mail().send(
                subject=f'[Tick数据检查{self.date}]请检查Tick数据是否更新完成，五分钟后重试',
                body_content=f'No tick data on {self.date}',
                receivers=[R.staff['ling']],
            )
            time.sleep(300)
            self.check_daily()

    def notify_with_email(self, check_result):
        alert_value = [check_result[key] for key in check_result.keys() if key != 'No Trade Info']
        if any(alert_value):
            subject = fr'[Alert !!!Daily Tick Check] {self.date} has error'
        else:
            subject = fr'[Daily Tick Check] {self.date}'
        content = f"""
        <table width="800" border="0" cellspacing="0" cellpadding="4">
        <tr>
        <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>Tick数据检查结果</b></td>
        </tr>
        <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
        """

        content += f"""
        <p><b>数据日期：{self.date}</b></p>
        <p><b>数据路径：{self.daily_dir}</b></p>
        <p><b>股票数量：{len(self.file_list)}</b></p>
        <p><b>文件缺失股票列表：{check_result['Missing Stock']}</b></p>
        <p><b>无交易信息股票列表：{check_result['No Trade Info']}</b></p>
        <p><b>无交易信息非停牌股票列表：{check_result['Unsuspended No Trade Info Stock']}</b></p>
        <p><b>0值股票列表：{check_result['Zero']}</b></p>
        <p><b>负值股票列表：{check_result['Negative']}</b></p>
        <p><b>缺失值股票列表：{check_result['NA']}</b></p>
        <p><b>高价低价不合理股票列表：{check_result['High']+check_result['Low']}</b></p>
        <p><b>成交量不合理股票列表：{check_result['Volume']+check_result['Amount']}</b></p>
        <p><b>买卖盘不合理股票列表：{check_result['Ask&Bid']}</b></p>
        <p><b>时间间隔不合理股票列表：{check_result['Time interval']}</b></p>
        """

        Mail().send(
            subject,
            content,
            attachs=[],
            pics=[],
            pic_disp=[],
            receivers=R.department['research'],
        )

    def multi_task_daily(self):
        chunked_list = np.array_split(self.file_list, 10)

        t1 = time.time()
        output = multi_task(
            func=self.check_multi_files,
            tasks=chunked_list,
            n_cpu=1,
        )
        t2 = time.time() - t1
        print(f'总耗时：{t2}秒')

        check_result = {key: sum([item[key] for item in output], []) for key in output[0].keys()}
        check_result = self.cross_check_with_choice(check_result)
        return check_result

    def cross_check_with_choice(self, check_result):
        ticker_list = [os.path.basename(file).split('_')[0] for file in self.file_list]
        ticker_list = [ticker.replace('XSHE', 'SZ').replace('XSHG', 'SH') for ticker in ticker_list]
        ticker_set = set(ticker_list)

        c.start()
        choice_ticker_set = set(c.sector("001004", f"{self.date}").Codes)
        missing_ticker_list = list(choice_ticker_set - ticker_set)
        check_result.update({'Missing Stock': missing_ticker_list})

        if check_result['No Trade Info']:
            suspension_info = c.css(','.join(check_result['No Trade Info']), "TRADESTATUS",
                                    f"TradeDate={self.date}").Data
            check_result.update({
                'Unsuspended No Trade Info Stock':
                    [ticker for ticker, status in suspension_info.items() if '停牌' not in status[0]]
            })
        else:
            check_result.update({'Unsuspended No Trade Info Stock': []})

        c.stop()
        return check_result

    def check_multi_files(self, file_path_list):
        multi_file_check_result = {}
        for file_path in file_path_list:
            check_result = self.check_single_tick(file_path)
            if multi_file_check_result == {}:
                multi_file_check_result.update(check_result)
            else:
                multi_file_check_result = {k: multi_file_check_result[k] + v
                                           for k, v in check_result.items()}
        return multi_file_check_result

    @staticmethod
    def check_single_tick(file_path):
        raw_df = pd.read_hdf(file_path, key='data')
        assert isinstance(raw_df, pd.DataFrame)
        df = raw_df.set_index('time', append=False).sort_index()
        ticker = os.path.basename(file_path).split('_')[0]
        error_dict = CheckMethod(df).check_dict
        check_result = {
            error: [ticker] for error, result in error_dict.items() if result
        }
        check_result.update({
            error: [] for error, result in error_dict.items() if not result
        })
        if any(check_result.values()):
            print(f'{file_path} has error')
        else:
            print(f'{file_path} is OK')
        return check_result


class CheckMethod:
    def __init__(self, df):
        df.index = df.index.astype('int64')
        self.new_df = df.query('time>=92500000').astype(float)
        if len(self.new_df.query('volume!=0')) != 0:
            first_non_zero_index = self.new_df.query('volume!=0').index[0]
            self.new_df = self.new_df.loc[first_non_zero_index:]
        else:
            self.new_df = self.new_df.query('volume!=0')
        self.check_list = ['NA', 'Zero', 'Negative', 'High', 'Low', 'Volume',
                           'Amount', 'Ask&Bid', 'No trade', 'Time interval']
        self.kline_col = ['last', 'high', 'low', 'volume', 'total_turnover']
        self.check_dict = {
            'NA': self.check_na(),
            'Zero': self.check_zero(),
            'Negative': self.check_negative(),
            'High': self.check_high(),
            'Low': self.check_low(),
            'Volume': self.check_volume(),
            'Amount': self.check_amount(),
            'Ask&Bid': self.check_ab(),
            'No Trade Info': self.check_no_trade(),
            'Time interval': self.check_time_interval(),
        }

    def check_na(self):
        return bool(self.new_df.isna().sum().sum())

    def check_zero(self):
        return bool((self.new_df[self.kline_col] == 0).sum().sum())

    def check_negative(self):
        return bool((self.new_df[self.kline_col] < 0).sum().sum())

    def check_high(self):
        return bool(len(self.new_df.query('high<last')))

    def check_low(self):
        return bool(len(self.new_df.query('low>last')))

    def check_volume(self):
        return any((self.new_df['volume'] < self.new_df['volume'].shift(1)))

    def check_amount(self):
        return any(self.new_df['total_turnover'] < self.new_df['total_turnover'].shift(1))

    def check_ab(self):
        pankou_p_col = ['b5', 'b4', 'b3', 'b2', 'b1', 'a1', 'a2', 'a3', 'a4', 'a5']
        ab_df = self.new_df[pankou_p_col]
        return not (((ab_df.query('~(b5<b4<b3<b2<b1<=a1<a2<a3<a4<a5)') == 0).any(axis=1)).all())

    def check_no_trade(self):
        return bool(len(self.new_df.query('volume!=0')) == 0)

    def check_time_interval(self):
        time_interval_s = self.new_df.index.to_series().diff() / 3000000
        time_interval_s = time_interval_s[(time_interval_s.index < 130000000) | (time_interval_s.index > 130020000)]
        return any(time_interval_s > 50)
