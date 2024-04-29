#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/17 10:00
# @Author  : Suying
# @Site    : 
# @File    : equity_check.py

import os
import time

import pandas as pd

from record.get_clearing_info import SettleInfo
from util.send_email import Mail, R
from record.account_info import read_terminal_info
from util.trading_calendar import TradingCalendar
from util.file_location import FileLocation


def send_equity_check(date=None):
    EquityCheck(date=date).notify_check_with_email()


class EquityCheck:
    def __init__(self, account=None, date=None):
        # self.account = [account] if account is not None else ['踏浪1号', '踏浪2号', '踏浪3号',
        #                                                       '盼澜1号', '听涟2号']

        self.account = [account] if account is not None else ['踏浪1号', '踏浪2号',
                                                              '盼澜1号', '听涟2号']


        last_trading_day = TradingCalendar().get_n_trading_day(time.strftime('%Y%m%d'), -1).strftime('%Y%m%d')
        self.date = date if date is not None else last_trading_day
        self.dir = FileLocation.clearing_dir
        self.account_path = rf'{FileLocation.remote_monitor_dir}\衍舟策略观察_{self.date}.xlsx'

    def notify_check_with_email(self):
        Mail().receive(save_dir=self.dir,
                       user='trading_1@yz-fund.com.cn',
                       pwd='BO6iJOUXZwDdndz0')
        file_list = SettleInfo(date=self.date).file_path_list
        missed_file_list = [f for f in file_list if not os.path.exists(f)]

        if missed_file_list:
            self.retry(missed_file_list)
        else:
            check_info_dict = {x: self.check_account_info(x) for x in self.account}
            email_info = self.gen_email_content(check_info_dict=check_info_dict)
            Mail().send(
                subject=email_info['subject'],
                body_content=email_info['content'],
                receivers=R.department['research'] + [R.department['tech'][0]],
            )

    def retry(self, missed_file_list):
        missed_string = '\n\n'.join(missed_file_list)
        print(f'{missed_string}不存在')
        Mail().send(
            subject=f'[各账户资产核对]{self.date}对账单文件缺失，10分钟后重试。',
            body_content=f'{missed_string}不存在',
            receivers=R.department['research'][0],
        )
        time.sleep(600)
        self.notify_check_with_email()

    def check_account_info(self, account):
        clearing_info = SettleInfo(date=self.date).get_settle_info(account=account)
        record_info = read_terminal_info(date=self.date, account=account)
        if account in ['弄潮1号', '弄潮2号']:
            info_df = self.gen_dict_to_df(clearing_info, record_info)
        else:
            clearing_info_s = pd.Series(clearing_info, name='对账单')
            record_info_s = pd.Series(record_info, name='导出单')
            info_df = pd.concat([clearing_info_s, record_info_s], axis=1)
        info_df['对账单'] = info_df['对账单'].astype(float)
        info_df['导出单'] = info_df['导出单'].astype(float)
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

    @staticmethod
    def gen_dict_to_df(settle_dict, record_dict):
        data = []
        for key, value in settle_dict.items():
            common_key = value.keys() & record_dict[key].keys()
            # common_key = [k for k in common_key if k not in ['成交额']]
            key_deduct = key.replace('账户', '')
            new_key = [f'{key_deduct}{k}' for k in common_key]
            settle = pd.Series([value[k] for k in common_key], index=new_key, name='对账单')
            record = pd.Series([record_dict[key][k] for k in common_key], index=new_key, name='导出单')
            df = pd.concat([settle, record], axis=1)
            data.append(df)
        df = pd.concat(data, axis=0)
        return df

    def gen_email_content(self, check_info_dict):
        string = '|'.join(self.account)
        subject = f'[Equity Check]{self.date}'
        content = f"""
        <table width="800" border="0" cellspacing="0" cellpadding="4">
        <tr>
        <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>{string} 资产核对结果</b></td>
        </tr>
        <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
        """
        for account in check_info_dict.keys():
            content += f"""
                <p><b>{account}账户核对结果：</b></p>
                <center>{check_info_dict[account]}</center>
            """
        return {'subject': subject, 'content': content}

    def get_record_info(self, account):
        record_df = pd.read_excel(self.account_path, sheet_name=account, index_col=0)
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
    send_equity_check()