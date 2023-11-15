#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/17 10:00
# @Author  : Suying
# @Site    : 
# @File    : account_cross_check.py

import os
import time

import pandas as pd

from account_check.get_clearing_info import SettleInfo
from util.send_email import Mail, R
from record.account_info import read_account_info
from util.trading_calendar import TradingCalendar as TC
from file_location import FileLocation as FL


class AccountCheck:
    def __init__(self, account=None, date=None):
        self.account = [account] if account is not None else ['talang1', 'talang2', 'talang3', 'panlan1', 'tinglian2']
        last_trading_day = TC().get_n_trading_day(time.strftime('%Y%m%d'), -1).strftime('%Y%m%d')
        self.date = date if date is not None else last_trading_day
        self.dir = FL().clearing_dir
        self.account_path = rf'~\Desktop\strategy_update\cnn策略观察_{self.date}.xlsx'
        self.account_name_dict = {
            'panlan1': '盼澜1号',
            'tinglian2': '听涟2号',
            'talang1': '踏浪1号',
            'talang2': '踏浪2号',
            'talang3': '踏浪3号',
        }

    def notify_check_with_email(self):
        Mail().receive(save_dir=self.dir)
        try:
            Mail().receive(save_dir=self.dir)
        except FileNotFoundError:
            print('Error in notify_check_with_email, retry in 2 minutes.')
            time.sleep(120)
            self.notify_check_with_email()

        missed_string = self.check_all_file_exist()
        if missed_string:
            print(f'{missed_string}不存在')
            Mail().send(
                subject=f'[各账户资产核对]{self.date}失败，两分钟后重试',
                body_content=f'{missed_string}不存在',
                receivers=R.department['research'][0],
            )
            time.sleep(120)
            self.notify_check_with_email()
        else:
            check_info_dict = self.check_all_account_info()
            email_info = self.gen_email_content(check_info_dict=check_info_dict)
            Mail().send(
                subject=email_info['subject'],
                body_content=email_info['content'],
                receivers=R.department['research']+[R.department['tech'][0]],
            )

    def check_all_file_exist(self):
        f = SettleInfo(date=self.date)
        file_list = f.file_path_list
        missed_file_list = []
        for file in file_list:
            if not os.path.exists(file):
                missed_file_list.append(file)
        missed_file_string = '\n'.join(missed_file_list)
        return missed_file_string

    def check_all_account_info(self):
        check_info_dict = {}
        for account in self.account:
            check_info_dict[account] = self.check_account_info(account=account)
        return check_info_dict

    def check_account_info(self, account):
        clearing_info = SettleInfo(date=self.date).get_settle_info(account=account)
        record_info = read_account_info(date=self.date, account=account)
        clearing_info_s = pd.Series(clearing_info, name='对账单')
        record_info_s = pd.Series(record_info, name='导出单')
        info_df = pd.concat([clearing_info_s, record_info_s], axis=1)
        info_df['差值'] = info_df['对账单'] - info_df['导出单']

        def highlight_diff(s):
            if abs(s) > 1000:
                return f'background-color: lightblue'
            else:
                return ''

        styled_info_df = info_df.style.applymap(highlight_diff, subset=['差值'])
        styled_info_df = styled_info_df.format(
            {'对账单': '{:.2f}', '导出单': '{:.2f}', '差值': '{:.2f}'})
        styled_info_df = styled_info_df.to_html(classes='table', escape=False)
        styled_info_df = styled_info_df.replace('<table',
                                                '<table style="border-collapse: collapse; border: 1px solid black;"')
        styled_info_df = styled_info_df.replace('<tr', '<tr style="border-bottom: 1px solid black;"')
        styled_info_df = styled_info_df.replace('<th', '<th style="border-right: 1px solid black;"')
        styled_info_df = styled_info_df.replace('<td', '<td style="border-right: 1px solid black;"')

        return styled_info_df

    def gen_email_content(self, check_info_dict):
        subject = f'[Equity Check]{self.date}'
        content = f"""
        <table width="800" border="0" cellspacing="0" cellpadding="4">
        <tr>
        <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>盼澜1号|听涟2号|踏浪1号|踏浪2号|踏浪3号 资产核对结果</b></td>
        </tr>
        <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
        """
        for account in check_info_dict.keys():
            content += f"""
                <p><b>{self.account_name_dict[account]}账户核对结果：</b></p>
                <center>{check_info_dict[account]}</center>
            """
        return {'subject': subject, 'content': content}

    def get_record_info(self, account):
        record_df = pd.read_excel(self.account_path, sheet_name=self.account_name_dict[account], index_col=0)
        record_df.index = record_df.index.astype(str)
        record_info_dict = {
            '股票市值': record_df.loc[self.date, '总市值'],
            '股票交易额': record_df.loc[self.date, '成交额'],
        }
        if account.startswith('踏浪'):
            record_info_dict.update({
                '股票权益': record_df.loc[self.date, '总资产'],
            })
        elif account in ['盼澜1号', '听涟2号']:
            record_info_dict.update({
                '期权权益': record_df.loc[self.date, '期权总权益'],
                '股票权益': record_df.loc[self.date, '股票资产总值'],
            })
        return record_info_dict


if __name__ == '__main__':
    ac = AccountCheck()
    ac.notify_check_with_email()
