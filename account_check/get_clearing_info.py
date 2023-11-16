#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/18 11:20
# @Author  : Suying
# @Site    : 
# @File    : get_settle_info.py

import os
import time

import pandas as pd
import numpy as np

from account_check.txt_data import TxtData
from util.send_email import Mail, R


class SettleInfo:
    def __init__(self, date=None):
        self.date = date if date is not None else time.strftime('%Y%m%d')
        self.dir = rf'{os.path.expanduser("~")}\Desktop\Data\Save\账户对账单'
        self.account_path = rf'C:\Users\Yz02\Desktop\strategy_update\cnn策略观察_{self.date}.xlsx'

        formatted_date = pd.to_datetime(self.date).strftime('%Y-%m-%d')
        # 普通股票账户
        self.stock_account_path = {
            '盼澜1号': rf'{self.dir}/衍舟盼澜1号-客户对账单-5600010056_{self.date}.xlsx',
            '踏浪1号': rf'{self.dir}/衍舟踏浪1号-客户对账单-887062000125_{self.date}.xlsx',
            '踏浪2号': rf'{self.dir}/060100078888-衍舟（海南）私募基金管理有限公司－衍舟踏浪2号中证500指增私募证券投资基金-普通客户-{formatted_date}.xls',
            '踏浪3号': rf'{self.dir}/190000612973普通对账单_{self.date}.txt',
        }
        # 期权账户
        self.option_account_path = {
            '盼澜1号': rf'{self.dir}/衍舟盼澜1号-个股期权对账单-9008023342_{self.date}.xlsx',
            '听涟2号 cats': rf'{self.dir}/衍舟听涟2号-个股期权对账单-9008023665_{self.date}.xlsx',
        }
        # 信用账户
        self.credit_account_path = {
            '踏浪1号': rf'{self.dir}/衍舟踏浪1号-融资融券账户对账单-8009302636_{self.date}.xlsx',
            '听涟2号': rf'{self.dir}/310310300343衍舟听涟2号{self.date}(两融).TXT',
            '盼澜1号': rf'{self.dir}/衍舟盼澜1号-融资融券账户对账单（含约定融资＆约定融券）-8009296565_{self.date}.xlsx',
        }
        self.file_path_list = list(self.stock_account_path.values()) + list(self.option_account_path.values()) + list(self.credit_account_path.values())

    def get_settle_info(self, account):
        print('获取对账单信息：', account)
        if account == '盼澜1号':
            info_dict = self.generate_panlan1_settle_info()
        elif account == '听涟2号':
            info_dict = self.generate_tinglian2_settle_info()
        elif account == '踏浪1号':
            info_dict = self.generate_talang1_settle_info()
        elif account == '踏浪2号':
            info_dict = self.generate_talang2_settle_info()
        elif account == '踏浪3号':
            info_dict = self.generate_talang3_settle_info()
        else:
            raise ValueError('Account name is not correct, '
                             'please input right account name.')

        for key, value in info_dict.items():
            if value == 'nan':
                print(f'{account}对账单 {key}存在缺失值，请检查后重新运行')
                Mail().send(
                    subject=f'{account}对账单 {key}存在缺失值，请检查后重新运行',
                    body_content=f'{account}对账单 {key}存在缺失值，请检查后重新运行',
                    receivers=R.department['research'][0],
                )
                raise ValueError(f'{account}对账单 {key}存在缺失值，请检查后重新运行')
            else:
                info_dict[key] = float(value)
        return info_dict

    def generate_tinglian2_settle_info(self):
        emc_stock_dict = TxtData(self.credit_account_path['听涟2号']).gen_settle_data()
        stock_equity = float(emc_stock_dict['资产信息'].loc[0, '总资产'])-float(emc_stock_dict['资产信息'].loc[0, '总负债'])
        stock_market_val = float(emc_stock_dict['资产信息'].loc[0, '当前市值'])
        stock_transaction_vol = emc_stock_dict['资产交割']['成交金额'].astype(float).sum()

        cats_option_df = pd.read_excel(self.option_account_path['听涟2号 cats'], sheet_name='Sheet1', index_col=0)
        cats_option_equity = float(cats_option_df.loc['总权益：'][0])
        cats_option_transaction_df = cats_option_df.loc['对账单':]
        cats_option_transaction_df = cats_option_transaction_df.rename(columns=cats_option_transaction_df.iloc[1])
        cats_option_transaction_df = cats_option_transaction_df[cats_option_transaction_df.index == self.date]
        cats_option_transaction_vol = cats_option_transaction_df['成交金额'].astype(float).abs().sum()

        info_dict = {
            '期权权益': cats_option_equity,
            '股票权益': stock_equity,
            '股票市值': stock_market_val,
            '成交额': stock_transaction_vol + cats_option_transaction_vol,
            '股票成交额': stock_transaction_vol,
            '期权成交额': cats_option_transaction_vol,
        }
        return info_dict

    def generate_panlan1_settle_info(self):
        stock_df = pd.read_excel(self.stock_account_path['盼澜1号'], sheet_name='Sheet1',
                                 index_col=0)
        putong_equity = stock_df.iloc[np.where(stock_df.values == '总资产')[0][0] + 1, np.where(stock_df.values == '总资产')[1][0]]
        putong_market_value = stock_df.iloc[
                np.where(stock_df.values == '资产市值')[0][0] + 1, np.where(stock_df.values == '资产市值')[1][0]]

        option_df = pd.read_excel(self.option_account_path['盼澜1号'], sheet_name='Sheet1')
        option_equity = option_df.iloc[
                np.where(option_df.values == '总权益：')[0][0], np.where(option_df.values == '总权益：')[1][0] + 1]

        option_transaction_loc = np.where(option_df.values == '对账单')
        option_transaction_df = option_df.iloc[option_transaction_loc[0][0]:]
        option_transaction_df = option_transaction_df.rename(columns=option_transaction_df.iloc[1]).iloc[2:]
        option_transaction_df = option_transaction_df.query('买卖方向 == "买入" or 买卖方向 == "卖出"')
        option_transaction_vol = option_transaction_df['成交金额'].astype(float).sum()

        putong_transaction_df = stock_df.copy()
        putong_transaction_df.columns = putong_transaction_df.loc['发生日期']
        putong_transaction_df = putong_transaction_df[putong_transaction_df.index == self.date]
        putong_stock_transaction_df = putong_transaction_df.query('摘要=="证券买入" or 摘要=="证券卖出"')
        putong_stock_transaction_vol = putong_stock_transaction_df['成交股数'].mul(putong_stock_transaction_df['成交价格']).sum()

        credit_df = pd.read_excel(self.credit_account_path['盼澜1号'], sheet_name='Sheet1',index_col=False)
        credit_equity = credit_df.iloc[np.where(credit_df.values == '净资产')[0][0]+1, np.where(credit_df.values == '净资产')[1][0]]
        credit_market_value = credit_df.iloc[np.where(credit_df.values == '证券市值')[0][0]+1,
                                             np.where(credit_df.values == '证券市值')[1][0]]

        credit_transaction_loc1 = np.where(credit_df.values == '业务类型')
        credit_transaction_df = credit_df.iloc[credit_transaction_loc1[0][0]:]
        credit_transaction_df = credit_transaction_df.rename(columns=credit_transaction_df.iloc[0]).iloc[1:]
        credit_transaction_df = credit_transaction_df.query('业务类型 == "证券买卖"')
        credit_stock_transaction_vol = credit_transaction_df['发生数量'].astype(float).mul(credit_transaction_df['成交价格'].astype(float)).sum()

        info_dict = {
            '期权权益': option_equity,
            '股票权益': putong_equity + credit_equity,
            '股票市值': putong_market_value + credit_market_value,
            '普通账户股票权益': putong_equity,
            '普通账户股票市值': putong_market_value,
            '信用账户股票权益': credit_equity,
            '信用账户股票市值': credit_market_value,
            '成交额': putong_stock_transaction_vol + credit_stock_transaction_vol + option_transaction_vol,
            '股票成交额': putong_stock_transaction_vol + credit_stock_transaction_vol,
            '期权成交额': option_transaction_vol,
        }
        return info_dict

    def generate_talang2_settle_info(self):
        stock_df = pd.read_excel(
            self.stock_account_path['踏浪2号'],
            sheet_name='普通对账单资金信息', index_col=False)
        location = np.where(stock_df.values == '资产总值')
        info_dict = {'股票权益': stock_df.iloc[location[0][0] + 1, location[1][0]]}

        def sep_df(start, end, df):
            loc_start = np.where(df.values == start)
            loc_end = np.where(df.values == end)
            new_df = df.iloc[loc_start[0][0] + 1:loc_end[0][0]].dropna(axis=1, how='all')
            new_df.columns = new_df.iloc[0]
            return new_df.iloc[1:]

        pos_df = sep_df('持仓信息', '多金融产品持仓：', stock_df)

        transaction_df = sep_df('资金流水明细', '债券回购预计利息', stock_df)

        info_dict.update({
            '股票市值': pos_df['市值'].astype(float).sum(),
            '成交额': transaction_df[transaction_df.业务标志名称.isin(['证券卖出', '证券买入'])]['成交金额'].astype(
                float).sum(),
        })
        return info_dict

    def generate_talang3_settle_info(self):
        f = TxtData(self.stock_account_path['踏浪3号'])
        settle_dict = f.gen_settle_data(encoding='utf-8')
        info_dict = {
            '股票权益': float(settle_dict['series']['总资产']),
            '股票市值': float(settle_dict['series']['当前证券市值']),
            '成交额': settle_dict['资金流水明细'].query('摘要.isin(["证券买入","证券卖出"])').成交金额.astype(
                float).sum(),

        }
        return info_dict

    def generate_talang1_settle_info(self):
        stock_df = pd.read_excel(self.stock_account_path['踏浪1号'], sheet_name='Sheet1', index_col=0)
        credit_df = pd.read_excel(self.credit_account_path['踏浪1号'], sheet_name='Sheet1', index_col=0)

        def get_loc(df, value, col=True):
            loc = np.where(df.values == value)
            if col:
                return loc[1][0]
            else:
                return loc[0][0]

        def get_loc_value(df, value):
            return df.iloc[get_loc(df, value, col=False) + 1, get_loc(df, value, col=True)]

        def get_transaction_vol(df, selected_cols, selected_values):
            new_df = df.iloc[:, [get_loc(df, col) for col in selected_cols]]
            new_df.columns = ['摘要', '成交股数', '成交价格']
            new_df = new_df.query('摘要 in @selected_values')
            return new_df['成交股数'].mul(new_df['成交价格']).sum()

        transaction_vol_stock = get_transaction_vol(stock_df, ['摘要', '成交股数', '成交价格'], ['证券买入', '证券卖出'])
        transaction_vol_credit = get_transaction_vol(credit_df, ['业务类型', '发生数量', '成交价格'], ['证券买卖'])
        info_dict = {
            '股票权益': get_loc_value(stock_df, '总资产') + get_loc_value(credit_df, '净资产'),
            '股票市值': get_loc_value(stock_df, '资产市值') + get_loc_value(credit_df, '证券市值'),
            '普通账户股票权益': get_loc_value(stock_df, '总资产'),
            '普通账户股票市值': get_loc_value(stock_df, '资产市值'),
            '信用账户股票权益': get_loc_value(credit_df, '净资产'),
            '信用账户股票市值': get_loc_value(credit_df, '证券市值'),
            '成交额': transaction_vol_credit + transaction_vol_stock,
        }
        return info_dict
