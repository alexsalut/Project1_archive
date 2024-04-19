# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 9:03
# @Author  : Youwei Wu, Suying Zhou
# @File    : product_update.py
# @Software: PyCharm

import os
import time
import pandas as pd

from util.send_email import Mail, R
from t.fq_kline import FqKLine
from util.file_location import FileLocation as FL


class KlineUpdater:
    def __init__(self, today=None):
        self.raw_dir = FL().raw_daily_dir
        self.save_path = FL().kline_path
        self.today = time.strftime('%Y%m%d') if today is None else today
        self.kc_path = self.save_path.replace('.pkl', '_kc.pkl')

    def update_confirm_adjusted_kline(self):
        self.update_adjusted_kline()
        self.generate_email()
        self.redownload_check()

    def redownload_check(self):
        if not os.path.exists(self.kc_path) or os.path.getsize(self.kc_path) <= 80000:
            print(f'{self.kc_path} does not exist or no sufficient data.')
            time.sleep(300)
            self.update_confirm_adjusted_kline()

    def generate_email(self):
        if os.path.exists(self.kc_path):
            subject = '[Adjusted Kline] Data finish processing'
            adjusted_kline = pd.read_pickle(self.save_path)
            print(f'{self.kc_path} exists.')
            info_dict = self.data_check(adjusted_kline)
            content = f"""
            <table width="800" border="0" cellspacing="0" cellpadding="4">
            <tr>
            <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>Adjusted Kline updated</b></td>
            </tr>
            <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
            <p>File path:</p>
            &nbsp&nbsp{self.save_path}
            <p>Number of A board stocks today:</p>
            &nbsp&nbsp{info_dict['Total Number of Stocks']}
            <p>NaN:</p> 
            &nbsp&nbsp{info_dict['NaN']}
            <p>Negative:</p> 
            &nbsp&nbsp{info_dict['Negative']}
            <p>Zero:</p> 
            &nbsp&nbsp{info_dict['Zero']}
            <p>Open&Close out of High&Low:</p> 
            &nbsp&nbsp{info_dict['Open&Close out of High&Low']}
            <p>Today Extreme High&Low Difference(>30%):</p> 
            &nbsp&nbsp{info_dict['Extreme High&Low Difference']}
            <p>Today Extreme daily Ret(>20.05%):</p> 
            &nbsp&nbsp{info_dict['Extreme daily Ret']}
            <p>Missing stocks compared with raw daily bar:</p>
            &nbsp&nbsp{info_dict['Missing stocks compared with Tushare']}
            """
        else:
            subject = '[Adjusted Kline] File is non-existent. Retry downloading in 5 minutes.'
            content = None

        Mail().send(subject=subject, body_content=content, receivers=R.department['research'])

    def data_check(self, adjusted_kline):
        keys = [
            'Total Number of Stocks',
            'NaN',
            'Negative',
            'Zero',
            'Open&Close out of High&Low',
            'Extreme High&Low Difference',
            'Extreme daily Ret',
            'Missing stocks compared with Tushare',
        ]
        info_dict = {key: self.df_check(adjusted_kline, option=key) for key in keys}
        return info_dict

    def df_check(self, adjusted_kline, option):
        print(option)
        if option == 'NaN':
            return adjusted_kline[adjusted_kline.isna()].dropna(how='all').index.tolist()
        elif option == 'Total Number of Stocks':
            return len(adjusted_kline.loc[self.today])
        elif option == 'Negative':
            return adjusted_kline[(adjusted_kline < 0)].iloc[:, [0, 1, 2, 3, 4, 5, -1]].dropna(how='all').index.tolist()
        elif option == 'Zero':
            df = (adjusted_kline.loc[:, :'amount'] == 0)
            return df[df].dropna().index.tolist()
        elif option == 'Open&Close out of High&Low':
            return adjusted_kline[(adjusted_kline['close'] > adjusted_kline['high']) |
                                  (adjusted_kline['open'] > adjusted_kline['high']) |
                                  (adjusted_kline['close'] < adjusted_kline['low']) |
                                  (adjusted_kline['open'] < adjusted_kline['low'])].dropna(how='all').index.tolist()
        elif option == 'Extreme High&Low Difference':
            today_kline = adjusted_kline.loc[self.today]

            return today_kline[
                (today_kline['high'] - today_kline['low']) / today_kline['low'] > 0.3].dropna(
                how='all').index.tolist()
        elif option == 'Extreme daily Ret':
            today_kline = adjusted_kline.loc[self.today]
            return today_kline.query('abs(pct_chg)>0.2005')['pct_chg'].apply(lambda x: f'{x:.2%}').index.tolist()
        elif option == 'Missing stocks compared with Tushare':
            raw_path = rf'{self.raw_dir}/{self.today[:4]}/{self.today[:6]}/raw_daily_{self.today}.csv'
            if os.path.exists(raw_path):
                raw_df = pd.read_csv(raw_path)
                kline = adjusted_kline.loc[self.today]
                raw_stock = raw_df['ts_code'].str[:6].tolist()
                kline_stock = [stock[2:] for stock in kline.index.tolist()]
                return list(set(raw_stock) - set(kline_stock))
            else:
                print(f'{raw_path} does not exist. Download raw daily bar first.')
        else:
            raise ValueError('Option not available')

    def update_adjusted_kline(self):
        FqKLine(
            tushare_dir=self.raw_dir,
            save_path=self.save_path,
        ).gen_qfq_kline()


if __name__ == '__main__':
    updater = KlineUpdater()
    updater.update_confirm_adjusted_kline()