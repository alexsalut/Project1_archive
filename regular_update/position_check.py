#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/22 16:58
# @Author  : Suying
# @Site    : 
# @File    : position.py

import time
import os
import pandas as pd

from util.send_email import Mail, R
from util.file_location import FileLocation as fl


def send_position_check(date=None):
    date = date if date is not None else time.strftime('%Y%m%d')
    account_list = ['踏浪1号', '盼澜1号', '听涟2号', '听涟1号', '踏浪3号']
    account_pos_dict = check_all_account_pos(account_list, date=date)
    subject = rf'[Position Check] {date}'
    content = gen_check_email_content(account_pos_dict, date)
    receivers = R.department['research'] + R.department['tech']
    Mail().send(subject=subject, body_content=content, receivers=receivers)


def check_all_account_pos(account_list, date=None):
    account_pos_dict = {}
    ap = AccountPosition
    for account in account_list:
        account_pos_dict[account] = check_account_pos(
            actual_pos_df=ap(account, date).get_actual_position(),
            target_pos_df=ap(account, date).get_target_position(),
        )
    return account_pos_dict


def gen_check_email_content(account_pos_dict, date):
    account_loc_dict = get_account_location(date)
    account_string = '|'.join(account_pos_dict.keys())

    content = f"""
    <table width="800" border="0" cellspacing="0" cellpadding="4">
    <tr>
    <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>{account_string} 持仓核对结果</b></td>
    </tr>
    <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
    """
    account_name_dict = {
        '踏浪1号': '踏浪1号信用账户',
        '盼澜1号': '盼澜1号信用账户',
        '听涟2号': '听涟2号信用账户',
        '踏浪3号': '踏浪3号普通账户',
        '听涟1号': '听涟1号财达股票账户',
    }
    for account in account_pos_dict.keys():
        content += f"""
            <p>{account_name_dict[account]}实际持仓文件路径：</p>
            &nbsp&nbsp{account_loc_dict[account]['actual']}
            <p>{account_name_dict[account]}目标持仓文件路径：</p>
            &nbsp&nbsp{account_loc_dict[account]['target']}
            <p>{account_name_dict[account]}实际持仓市值：</p>
            &nbsp&nbsp<font color=red>{account_pos_dict[account]['market val total']:.1f}</font>
            <p><b>{account_name_dict[account]}持仓核对结果：</b></p>
            <center>{account_pos_dict[account]['pos df']}</center>
        """
    return content


def check_account_pos(actual_pos_df, target_pos_df):
    pos_df = actual_pos_df.merge(target_pos_df, how='outer', left_index=True, right_index=True)
    pos_df = pos_df.fillna(0)
    pos_df['实际-目标'] = pos_df['实际'] - pos_df['目标']
    pos_df['偏移比率%'] = (100 * (pos_df['实际'] - pos_df['目标']) / pos_df['目标']).round(1)
    pos_df = pos_df.sort_values(by='市值', ascending=False)[['名称', '实际', '目标', '实际-目标', '偏移比率%', '市值']]
    market_val_total = pos_df['市值'].sum().round(2)
    pos_df['市值'] = pos_df['市值'].astype('int64', errors='ignore')
    filtered_pos_df = pos_df.query('实际!=0 or 目标!=0', engine='python')
    filtered_pos_df = filtered_pos_df.reset_index(drop=False)
    filtered_pos_df.index = filtered_pos_df.index + 1

    def highlight_diff(s):
        if s >= 200:
            return f'background-color: red'
        elif s <= -200:
            return f'background-color: green'
        elif abs(s) >= 100:
            return f'background-color: lightblue'
        else:
            return ''

    styled_pos_df = filtered_pos_df.style.applymap(highlight_diff, subset=['实际-目标', '偏移比率%'])
    styled_pos_df = styled_pos_df.format(
        {'实际': '{:.0f}', '目标': '{:.0f}', '实际-目标': '{:.0f}', '偏移比率%': '{:.1f}'})
    styled_pos_df = styled_pos_df.to_html(classes='table', escape=False)
    styled_pos_df = styled_pos_df.replace('<table',
                                          '<table style="border-collapse: collapse; border: 1px solid black;"')
    styled_pos_df = styled_pos_df.replace('<tr', '<tr style="border-bottom: 1px solid black;"')
    styled_pos_df = styled_pos_df.replace('<th', '<th style="border-right: 1px solid black;"')
    styled_pos_df = styled_pos_df.replace('<td', '<td style="border-right: 1px solid black;"')

    pos_dict = {
        'pos df': styled_pos_df,
        'market val total': market_val_total
    }
    return pos_dict


def get_account_location(date=None):
    formatted_date1 = time.strftime('%Y%m%d') if date is None else pd.to_datetime(date).strftime("%Y%m%d")
    formatted_date2 = time.strftime('%Y-%m-%d') if date is None else pd.to_datetime(date).strftime("%Y-%m-%d")
    account_position_dict = {
        '盼澜1号': {
            'actual': rf"{fl.account_dir['盼澜1号']}/CreditPosition_{formatted_date2}.csv",
            'target': rf'{fl.remote_target_pos_dir}/tag_pos_盼澜1号信用账户_{formatted_date1}.csv',
        },
        '听涟2号': {
            'actual': rf"{fl.account_dir['听涟2号 emc']}/310310300343_RZRQ_POSITION.{formatted_date1}.csv",
            'target': rf'{fl.remote_target_pos_dir}/tag_pos_听涟2号信用账户_{formatted_date1}.csv',
        },
        '踏浪1号': {
            'actual': rf"{fl.account_dir['踏浪1号']}/CreditPosition_{formatted_date2}.csv",
            'target': rf'{fl.remote_target_pos_dir}/tag_pos_踏浪1号信用账户_{formatted_date1}.csv',
        },
        '踏浪3号': {
            'actual': rf"{fl.account_dir['踏浪3号']}/PositionStatics-{formatted_date1}.csv",
            'target': rf'{fl.remote_target_pos_dir}/tag_pos_踏浪3号普通账户_{formatted_date1}.csv',
        },
        '听涟1号': {
            'actual': rf"{fl.account_dir['听涟1号 cd']}/PositionStatics-{formatted_date1}.csv",
            'target': rf'{fl.remote_target_pos_dir}/tag_pos_听涟1号财达股票账户_{formatted_date1}.csv',
        },

        '踏浪2号': {
            'actual': rf"{fl.account_dir['踏浪2号']}/PositionStatics-{formatted_date1}.csv",
            'target': rf'{fl.remote_target_pos_dir}/tag_pos_踏浪2号普通账户_{formatted_date1}.csv',
        }

    }
    return account_position_dict


class AccountPosition:
    def __init__(self, account, date=None):
        self.account = account
        self.date = date if date is not None else time.strftime('%Y%m%d')
        self.col_dict = self.get_position_col()
        self.location_dict = get_account_location(self.date)[self.account]

    def get_target_position(self):
        if os.path.exists(self.location_dict['target']):
            target_df = pd.read_csv(
                self.location_dict['target'],
                index_col=False,
                header=0,
                names=['代码', '目标'],
                dtype={'代码': str, '目标': 'Int64'},
            ).set_index('代码')
            target_df.index = target_df.index.str[2:]
            return target_df
        else:
            print(f'Error: {self.location_dict["target"]} does not exist')
            raise FileNotFoundError

    def get_actual_position(self):
        encoding = 'gbk' if self.account in ['听涟2号', '踏浪3号', '听涟1号', '踏浪2号'] else None
        if os.path.exists(self.location_dict['actual']):
            actual_df = pd.read_csv(
                self.location_dict['actual'],
                encoding=encoding,
            ).astype({
                self.col_dict['actual code']: str,
                self.col_dict['actual name']: str,
                self.col_dict['actual']: 'Int64',
                self.col_dict['actual market val']: 'float64',
            })

            if self.account != '听涟2号':
                account_col = self.col_dict['actual account']
                actual_df[account_col] = actual_df[account_col].astype('Int64')

            actual_df = actual_df.rename(columns={
                self.col_dict['actual code']: '代码',
                self.col_dict['actual name']: '名称',
                self.col_dict['actual']: '实际',
                self.col_dict['actual account']: '账户',
                self.col_dict['actual market val']: '市值'}).set_index('代码')
            actual_df.index = actual_df.index.str.zfill(6)
            if '账户' in actual_df.columns:
                actual_df = actual_df.query(f'账户=={fl.account_code[self.account]}')
            actual_df = actual_df[['名称', '实际', '市值']]
            return actual_df[actual_df['实际'] != 0]
        else:
            print(f'Error: {self.location_dict["actual"]} does not exist')
            raise FileNotFoundError

    def get_position_col(self):
        # 普通账户目前有三种，分别是盼澜1号，踏浪1号，听涟2号
        account_col_dict = {
            '盼澜1号': {
                'actual code': '代码',
                'actual name': '名称',
                'actual': '当前余额',
                'actual market val': '参考市值',
                'actual account': '账户',
                'target code': '代码',
                'target': '目标',
            },
            '听涟2号': {
                'actual code': '证券代码',
                'actual name': '证券名称',
                'actual account': '资金账号',
                'actual': '持仓数量',
                'actual market val': '市值',
            },
            '踏浪3号': {
                'actual code': '证券代码',
                'actual name': '证券名称',
                'actual': '当前拥股',
                'actual account': '资金账号',
                'actual market val': '市值',

            },
            '听涟1号': {
                'actual code': '证券代码',
                'actual name': '证券名称',
                'actual': '当前拥股',
                'actual account': '资金账号',
                'actual market val': '市值',
            },
        }
        account_col_dict['踏浪1号'] = account_col_dict['盼澜1号']
        account_col_dict['踏浪2号'] = account_col_dict['踏浪3号']
        if self.account in account_col_dict.keys():
            return account_col_dict[self.account]
        else:
            raise ValueError(f'Error: account {self.account} is not supported')
