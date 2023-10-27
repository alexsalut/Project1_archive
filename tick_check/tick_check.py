import os
import time
import numpy as np
import pandas as pd
import glob
from util.send_email import Mail, R
from util.utils import multi_task
from EmQuantAPI import c


class CheckTick:
    def __init__(self, date=None):
        self.tick_dir = r'\\192.168.1.251\h\data\RiceQuant\stock\ticks'
        self.record_path = r'check_results.txt'
        self.date = date if date is not None else time.strftime('%Y%m%d')
        self.daily_dir = rf'{self.tick_dir}/{self.date[:4]}/{self.date[:6]}/{self.date}'

    def multi_task_daily_check(self):
        info_dict = self.multi_task_daily()
        self.notify_with_email(info_dict)

    def multi_task_daily(self):
        file_path_list = glob.glob(rf'{self.daily_dir}/*.h5')
        num_stocks = len(file_path_list)

        chunked_list = np.array_split(file_path_list, 10)

        t1 = time.time()
        output = multi_task(self.check_multi_files, chunked_list, 10)
        t2 = time.time() - t1
        all_error_file_list = [item['error file list'] for item in output if item['error file list'] != []]
        all_error_file_list = [item for sublist in all_error_file_list for item in sublist]
        no_data_list = [stock for item in output for stock in item['no data list'] if item['no data list'] != []]
        no_data_unsuspended_list = [stock for item in output for stock in item['no data unsuspended list'] if item['no data unsuspended list'] != []]

        print(f'总耗时：{t2}秒')
        return {
            'stock count': num_stocks,
            'error file list': all_error_file_list,
            'no data list': no_data_list,
            'no data unsuspended list': no_data_unsuspended_list,
        }

    def check_multi_files(self, file_path_list):
        error_file_list = []
        no_data_list = []
        no_data_unsuspended_list = []
        for file_path in file_path_list:
            error_dict = self.check_single_tick(file_path)
            if 'No Data' in error_dict.keys():
                no_data_list.append(error_dict['No Data'])
                print(f'{file_path} has no data')
                if not self.check_suspension(error_dict['No Data'], self.date):
                    no_data_unsuspended_list.append(error_dict['No Data'])

            elif error_dict == {}:
                print(f'{file_path} is OK')
            else:
                error_file_list.append(file_path)
                print(f'{file_path} has error')
        return {
            'error file list': error_file_list,
            'no data list': no_data_list,
            'no data unsuspended list': no_data_unsuspended_list,
        }

    def notify_with_email(self, info_dict):
        subject = fr'[Daily Tick Check] {self.date}'
        content = f"""
        <table width="800" border="0" cellspacing="0" cellpadding="4">
        <tr>
        <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>Tick数据检查结果</b></td>
        </tr>
        <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
        """

        content += f"""
        <p><b>Tick数据检查日期：</b></p>
        <p><b>{self.date}</b></p>
        <p><b>Tick数据检查路径：</b></p>
        <p><b>{self.daily_dir}</b></p>
        <p><b>Tick数据检查股票数量：</b></p>
        <p><b>{info_dict['stock count']}</b></p>
        <p><b>Tick数据检查无数据股票列表：</b></p>
        <p><b>{info_dict['no data list']}</b></p>
        <p><b>Tick数据检查无数据非停牌股票列表：</b></p>
        <p><b>{info_dict['no data unsuspended list']}</b></p>
        
        """

        content += f"""
        <p><b>Tick数据检查有问题股票列表如下：</b></p>
        """
        for file_path in info_dict['error file list']:
            stock_code = os.path.basename(file_path[0]).split('_')[0]
            content += f"""
            <p><font color="#9900FF" >{stock_code}</font></p>
            """
        Mail().send(
            subject,
            content,
            attachs=[],
            pics=[],
            pic_disp=[],
            receivers=[R.staff['zhou'],R.staff['wu'] ]
        )

    def check_single_tick(self, file_path):
        df = pd.read_hdf(file_path, 'data').set_index('time', append=False).sort_index()
        if len(df.query('high!=0')) == 0:
            ticker = os.path.basename(file_path).split('_')[0].replace('XSHE', 'SZ').replace('XSHG', 'SH')
            return {'No Data': ticker}


        first_non_zero_index = df.query('high!=0').index[0]
        df = df.loc[first_non_zero_index:]
        kline_col = ['last', 'high', 'low', 'volume', 'total_turnover']

        pankou_p_col = ['b5', 'b4', 'b3', 'b2', 'b1', 'a1', 'a2', 'a3', 'a4', 'a5']
        ab_df = df[pankou_p_col]
        ab_is_ok = (ab_df.query('~(b5<b4<b3<b2<b1<=a1<a2<a3<a4<a5)') == 0).any(axis=1).all()
        ab_is_ok = int(not ab_is_ok)

        check_dict = {
            'NA': df.isna().sum().sum(),
            'Zero': (df[['last', 'high', 'low', 'volume', 'total_turnover']] == 0).sum().sum(),
            'Negative': (df[kline_col] < 0).sum().sum(),
            'High': len(df.query('high<last')),
            'Low': len(df.query('low>last')),
            'Volume': (df['volume'] < df['volume'].shift(1)).sum(),
            'total turnover': int(any(df['total_turnover'] < df['total_turnover'].shift(1))),
            'ab': ab_is_ok,
        }
        error_dict = {k: v for k, v in check_dict.items() if v != 0}
        return error_dict

    def check_suspension(self, ticker, date):
        c.start()
        data = c.css(ticker, "TRADESTATUS", f"TradeDate={date}").Data[ticker][0].count('停牌')
        c.stop()
        return bool(data)


if __name__ == '__main__':
    CheckTick('20231026').multi_task_daily_check()
