# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 9:03
# @Author  : Youwei Wu, Suying Zhou
# @File    : product_update.py
# @Software: PyCharm

import os
import time
import pandas as pd

from EmQuantAPI import c

from util.send_email import Mail, R
from util.file_location import FileLocation as fl


class KC50WeightUpdater:
    def __init__(self, today=None):
        self.save_dir = fl.kc50_weight_dir
        self.today = time.strftime('%Y%m%d') if today is None else today

    def kc50_weight_update_and_confirm(self):
        self.download_history_kc50_weight(start_date='20200909', end_date=self.today)
        save_path = os.path.join(self.save_dir, f'{self.today}.pkl')
        self.kc50_redownload_check(save_path=save_path)

    def kc50_redownload_check(self, save_path):
        error_list = self.kc50_weight_check(save_path=save_path)
        if len(error_list) == 0:
            print(f'[kc50 weight] no error found, downloaded successfully')
            subject = f'[kc50 weight] downloaded successfully'
            content = f"""
            <table width="800" border="0" cellspacing="0" cellpadding="4">
            <tr>
            <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>KC50 Weight generated successfully</b></td>
            </tr>
            <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
            <p>Download path:</p>
            {save_path}
            """
            Mail().send(subject=subject,
                        body_content=content,
                        # receivers=R.department['research'],
                        receivers=R.staff['zhou']
                        )
        else:
            print(f'[kc50 weight] error found, retry downloading in 10 seconds')
            time.sleep(10)
            self.kc50_weight_update_and_confirm()

    @staticmethod
    def kc50_weight_check(save_path):
        error_list = []
        if os.path.exists(save_path):
            kc50_df = pd.read_pickle(save_path)
            if kc50_df.empty:
                error_list.append(f'[kc50 weight check]{save_path} is empty')
            else:
                if abs(kc50_df.WEIGHT.sum() - 1) > 0.00001:
                    error_list.append(f'[kc50 weight check]{save_path} weight sum is not 1')
                if kc50_df.shape[0] != 50:
                    error_list.append(f'[kc50 weight check]{save_path} weight count is not 50')
                if not all(value > 0 for value in kc50_df.WEIGHT):
                    error_list.append(f'[kc50 weight check]{save_path} weight has negative value')
        else:
            error_list.append(f'[kc50 weight check]{save_path} does not exist')
        return error_list

    def download_history_kc50_weight(self, start_date, end_date):
        c.start()
        trade_dates = c.tradedates(
            startdate=start_date,
            enddate=end_date,
            options="period=1,order=1,market=CNSESH",
        ).Dates
        trade_dates = pd.to_datetime(trade_dates).strftime('%Y%m%d')
        for date in trade_dates:
            save_path = os.path.join(self.save_dir, f'{date}.pkl')
            if not os.path.exists(save_path):
                self.c_download_kc50_weight(date, save_path)
            else:
                print(f'[kc50 weight] {save_path} exists')
        c.stop()

    def c_download_kc50_weight(self, date, save_path):
        os.makedirs(self.save_dir, exist_ok=True)
        self.c_download_index_weight(
            index_ticker='000688.SH',
            date=date,
            save_path=save_path
        )

    @staticmethod
    def c_download_index_weight(index_ticker, date, save_path):
        print("Downloading Index Composition Weight")
        print("-----------------------------------")

        df = c.ctr(
            "INDEXCOMPOSITION",
            "SECUCODE,WEIGHT",
            f"IndexCode={index_ticker},EndDate={date},ispandas=1",
        )
        df.to_pickle(save_path)
        print(f'[{index_ticker} weight] {date} file has downloaded.')


if __name__ == '__main__':
    KC50WeightUpdater().kc50_weight_update_and_confirm()
