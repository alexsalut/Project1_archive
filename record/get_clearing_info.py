#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/18 11:20
# @Author  : Suying
# @Site    : 
# @File    : get_settle_info.py

import os
import time

import pandas as pd

from record.clearing_file_reader import read_clearing_file


class SettleInfo:
    def __init__(self, date=None):
        self.date = date if date is not None else time.strftime('%Y%m%d')
        self.dir = rf'{os.path.expanduser("~")}\Desktop\Data\Save\账户对账单'
        self.account_path = rf'C:\Users\Yz02\Desktop\strategy_update\cnn策略观察_{self.date}.xlsx'
        # 普通股票账户
        self.normal_account_path = {
            '踏浪1号': rf'{self.dir}/衍舟踏浪1号-客户对账单-887062000125_{self.date}.xlsx',
            '踏浪2号': rf'{self.dir}/华安证券账户对账单+衍舟踏浪2号+6030001882+{self.date}.xls',
            '踏浪3号': rf'{self.dir}/190000612973普通对账单_{self.date}.txt',
            '弄潮1号cats': rf'{self.dir}/衍舟弄潮1号-客户对账单-7200001295_{self.date}.xlsx',
            '弄潮1号matic': rf'{self.dir}/666810075512_衍舟弄潮1号_普通账单_HT1_{self.date}.xlsx',
            '弄潮2号': rf'{self.dir}/666810066802_衍舟弄潮2号_普通账单_HT1_{self.date}.xlsx'
        }
        # 期权账户
        self.option_account_path = {
            '盼澜1号': rf'{self.dir}/衍舟盼澜1号-个股期权对账单-9008023342_{self.date}.xlsx',
            '听涟2号': rf'{self.dir}/衍舟听涟2号-个股期权对账单-9008023665_{self.date}.xlsx',
            '弄潮1号': rf'{self.dir}/衍舟弄潮1号-个股期权对账单-9008023990_{self.date}.xlsx',
            '踏浪1号': rf'{self.dir}/衍舟踏浪1号-个股期权对账单-9008024407_{self.date}.xlsx',
        }


        self.future_account_path = {
            '弄潮1号matic': rf'{self.dir}/80012902-{self.date}.zip',
            '弄潮2号matic': rf'{self.dir}/80012903-{self.date}.zip'
        }

        # 信用账户
        self.credit_account_path = {
            '踏浪1号': rf'{self.dir}/衍舟踏浪1号-融资融券账户对账单-8009302636_{self.date}.xlsx',
            '听涟2号': rf'{self.dir}/310310300343衍舟听涟2号{self.date}(两融).TXT',
            '盼澜1号': rf'{self.dir}/衍舟盼澜1号-融资融券账户对账单（含约定融资＆约定融券）-8009296565_{self.date}.xlsx',
            '弄潮1号': rf'{self.dir}/衍舟弄潮1号-融资融券账户对账单（含约定融资＆约定融券）-8009286755_{self.date}.xlsx',
            '弄潮2号': rf'{self.dir}/960000192208_衍舟弄潮2号_两融账单_HT1_{self.date}.xlsx'
        }
        self.file_path_list = list(self.normal_account_path.values()) + list(self.option_account_path.values()) + list(
            self.credit_account_path.values())

    def get_settle_info(self, account):
        sep = '*' * 12
        print(sep, '获取对账单信息：', account, sep)
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
        elif account == '弄潮1号':
            info_dict = self.generate_nongchao1_settle_info()
        elif account == '弄潮2号':
            info_dict = self.generate_nongchao2_settle_info()
        else:
            raise ValueError('Account name is not correct, '
                             'please input right account name.')
        print(f'[{account}对账单信息]\n')
        for key, value in info_dict.items():
            print(key, ':', value, '\n')

        return info_dict

    def generate_tinglian2_settle_info(self):
        emc_stock_account = read_clearing_file(self.credit_account_path['听涟2号'], '东财信用账户')
        cats_option_account = read_clearing_file(self.option_account_path['听涟2号'], '中信期权账户')

        info_dict = {
            '期权权益': cats_option_account['账户净资产'],
            '股票权益': emc_stock_account['账户净资产'],
            '股票市值': emc_stock_account['账户证券市值'],
            '成交额': emc_stock_account['成交额'] + cats_option_account['成交额'],
            '股票成交额': emc_stock_account['成交额'],
            '期权成交额': cats_option_account['成交额'],
        }
        return info_dict

    def generate_panlan1_settle_info(self):
        cats_option_account = read_clearing_file(self.option_account_path['盼澜1号'], '中信期权账户')
        cats_credit_account = read_clearing_file(self.credit_account_path['盼澜1号'], '中信信用账户')

        info_dict = {
            '期权权益': cats_option_account['账户净资产'],
            '股票权益': cats_credit_account['账户净资产'],
            '股票市值': cats_credit_account['账户证券市值'],
            '信用账户股票权益': cats_credit_account['账户净资产'],
            '信用账户股票市值': cats_credit_account['账户证券市值'],
            '成交额': cats_credit_account['成交额'] + cats_option_account['成交额'],
            '股票成交额': cats_credit_account['成交额'],
            '期权成交额': cats_option_account['成交额'],
        }
        return info_dict

    def generate_talang2_settle_info(self):
        qmt_dict = read_clearing_file(self.normal_account_path['踏浪2号'], '华安普通账户')
        info_dict = {
            '股票权益': qmt_dict['账户净资产'],
            '股票市值': qmt_dict['账户证券市值'],
            '成交额': qmt_dict['成交额']
        }
        return info_dict

    def generate_talang3_settle_info(self):
        account_dict = read_clearing_file(self.normal_account_path['踏浪3号'], '国信普通账户')
        info_dict = {
            '股票权益': account_dict['账户净资产'],
            '股票市值': account_dict['账户证券市值'],
            '成交额': account_dict['成交额']
        }
        return info_dict

    def generate_talang1_settle_info(self):
        cats_option_account = read_clearing_file(self.option_account_path['踏浪1号'], '中信期权账户')
        cats_credit_account = read_clearing_file(self.credit_account_path['踏浪1号'], '中信信用账户')

        info_dict = {
            '期权权益': cats_option_account['账户净资产'],
            '股票权益': cats_credit_account['账户净资产'],
            '股票市值': cats_credit_account['账户证券市值'],
            '信用账户股票权益': cats_credit_account['账户净资产'],
            '信用账户股票市值': cats_credit_account['账户证券市值'],
            '成交额': cats_credit_account['成交额'] + cats_option_account['成交额'],
            '股票成交额': cats_credit_account['成交额'],
            '期权成交额': cats_option_account['成交额'],
        }

        return info_dict

    def generate_nongchao1_settle_info(self):
        cats_normal = read_clearing_file(self.normal_account_path['弄潮1号cats'], '中信普通账户')
        cats_credit = read_clearing_file(self.credit_account_path['弄潮1号'], '中信信用账户')
        matic_normal = read_clearing_file(self.normal_account_path['弄潮1号matic'], '华泰普通账户')
        matic_future = read_clearing_file(self.future_account_path['弄潮1号matic'], '华泰期货账户')
        cats_option = read_clearing_file(self.option_account_path['弄潮1号'], '中信期权账户')
        info_dict = {
            '华泰普通账户': matic_normal,
            '中信普通账户': cats_normal,
            '中信信用账户': cats_credit,
            '华泰期货账户': matic_future,
            '中信期权账户': cats_option
        }
        return info_dict

    def generate_nongchao2_settle_info(self):
        matic_normal = read_clearing_file(self.normal_account_path['弄潮2号'], '华泰普通账户')
        matic_credit = read_clearing_file(self.credit_account_path['弄潮2号'], '华泰信用账户')
        matic_future = read_clearing_file(self.future_account_path['弄潮2号matic'], '华泰期货账户')
        info_dict = {
            '华泰普通账户': matic_normal,
            '华泰信用账户': matic_credit,
            '华泰期货账户': matic_future
        }
        return info_dict

if __name__ == '__main__':


    print(SettleInfo('20240415').get_settle_info('踏浪2号'))