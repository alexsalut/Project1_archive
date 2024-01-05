#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/21 11:29
# @Author  : Suying
# @Site    : 
# @File    : clearing_file_reader.py
import pandas as pd
import numpy as np
import rqdatac as rq
from util.txt_data import TxtData


def read_clearing_file(path, account):
    if account == '中信普通账户':
        return read_cats_normal_account(path)
    elif account == '中信信用账户':
        return read_cats_credit_account(path)
    elif account == '华泰普通账户':
        return read_matic_normal_account(path)
    elif account == '华泰信用账户':
        return read_matic_credit_account(path)
    elif account == '中信期权账户':
        return read_cats_option_acccount(path)
    elif account == '东财信用账户':
        return read_emc_credit_account(path)
    elif account == '广发普通账户':
        return read_qmt_normal_account(path)
    elif account == '国信普通账户':
        return read_iquant_normal_account(path)


def read_iquant_normal_account(path):
    # 国信证券普通账户
    # 文件命名格式 190000612973普通对账单_20231120.txt
    f = TxtData(path)
    settle_dict = f.gen_settle_data(encoding='utf-8')
    account_dict = {
        '账户净资产': float(settle_dict['series']['总资产']),
        '账户证券市值': float(settle_dict['series']['当前证券市值']),
        '成交额': settle_dict['资金流水明细'].query('摘要.isin(["证券买入","证券卖出"])').成交金额.astype(
            float).sum(),
    }
    return account_dict


def read_qmt_normal_account(path):
    # 广发普通账户对账单
    # 060100078888-衍舟（海南）私募基金管理有限公司－衍舟踏浪2号中证500指增私募证券投资基金-普通客户-2023-11-20.xlsx
    stock_df = pd.read_excel(path, sheet_name='普通对账单资金信息', index_col=False)
    account_dict = {'账户净资产': get_value(stock_df, '资产总值')}
    pos_df = sep_df('持仓信息', '多金融产品持仓：', stock_df)
    transaction_df = sep_df('资金流水明细', '债券回购预计利息', stock_df)
    account_dict.update({
        '账户证券市值': pos_df['市值'].astype(float).sum(),
        '成交额': transaction_df[transaction_df.业务标志名称.isin(['证券卖出', '证券买入'])]['成交金额'].astype(
            float).sum(),
    })
    return account_dict


def read_emc_credit_account(path):
    # 读取东财信用账户的资产信息
    # 文件名格式: 310310300343衍舟听涟2号20231120(两融).TXT
    emc_stock_dict = TxtData(path).gen_settle_data()
    account_dict = {
        '账户净资产': float(emc_stock_dict['资产信息'].loc[0, '总资产']) - float(
            emc_stock_dict['资产信息'].loc[0, '总负债']),
        '账户总负债': float(emc_stock_dict['资产信息'].loc[0, '总负债']),
        '账户证券市值': float(emc_stock_dict['资产信息'].loc[0, '当前市值']),
        '成交额': emc_stock_dict['资产交割']['成交金额'].astype(float).sum()
    }
    return account_dict


def read_cats_option_acccount(path):
    date = path.split('_')[1].split('.')[0]
    account_dict = {}

    cats_option_df = pd.read_excel(path, sheet_name='Sheet1', index_col=False)
    account_dict['账户净资产'] = float(get_value(cats_option_df, '总权益：', vertical=False))
    account_dict['账户证券市值'] = float(get_value(cats_option_df, '期权市值：', vertical=False))

    transaction_loc = np.where(cats_option_df.values == '对账单')
    cats_option_transaction_df = cats_option_df.iloc[transaction_loc[0][0]:]
    cats_option_transaction_df = cats_option_transaction_df.rename(columns=cats_option_transaction_df.iloc[1])
    cats_option_transaction_df = cats_option_transaction_df.query(f'发生日期 == "{date}"')
    account_dict['成交额'] = cats_option_transaction_df['成交金额'].astype(float).abs().sum()
    return account_dict


def read_cats_normal_account(path):
    # 读取中信普通账户的资产信息
    # 文件名格式: 衍舟基金名-客户对账单-5600010056_20231022.xlsx
    normal_df = pd.read_excel(path, sheet_name='Sheet1',
                             index_col=None)
    account_dict = {}
    account_dict['账户净资产'] = get_value(normal_df, '总资产')
    account_dict['资金余额'] = get_value(normal_df, '资金余额')

    normal_transaction_df = sep_df(start='对账单', end='当日持仓清单', df=normal_df)
    normal_security_transaction_df = normal_transaction_df[normal_transaction_df['摘要'].isin(['证券买入', '证券卖出'])]
    account_dict['成交额'] = normal_security_transaction_df['成交股数'].mul(
        normal_security_transaction_df['成交价格']).sum()
    account_dict['成交额（含费）'] = abs(normal_security_transaction_df['发生金额']).sum()

    asset_df = sep_df('当日持仓清单', '新股配号', normal_df)
    account_dict = update_asset(account_dict, asset_df, '证券代码', '证券名称', '参考市值')
    return account_dict


def read_cats_credit_account(path):
    # 读取中信信用账户的资产信息
    # 文件名格式: 衍舟踏浪1号-融资融券账户对账单-8009302636_20231120.xlsx
    credit_df = pd.read_excel(path, sheet_name='Sheet1', index_col=False)
    account_dict = {}

    account_dict['账户净资产'] = get_value(credit_df, '净资产')
    account_dict['账户总资产'] = get_value(credit_df, '总资产')
    account_dict['账户总负债'] = account_dict['账户总资产'] - account_dict['账户净资产']
    account_dict['账户证券市值'] = get_value(credit_df, '证券市值')
    account_dict['维担比例'] = float(get_value(credit_df, '维持担保比例：', vertical=False))
    account_dict['资金余额'] = get_value(credit_df, '资金余额')

    # 负债信息
    debt_df = sep_df(start='2、负债情况', end='3、融资融券负债明细(合并对账单)', df=credit_df).iloc[0]
    account_dict['融资负债'] = debt_df['融资余额']
    account_dict['融券负债'] = debt_df['融券市值']
    account_dict['融资融券费用'] = debt_df['融资费用'] + debt_df['融券费用']

    # 读取资产持仓信息
    asset_df = sep_df(start='1.2证券余额', end='2、负债情况', df=credit_df)
    account_dict = update_asset(account_dict, asset_df, '证券代码', '证券简称', '当前市值')

    # 读取成交信息
    credit_transaction_df = sep_df(start='三、业务流水(合并对账单)', df=credit_df)
    credit_transaction_df = credit_transaction_df[credit_transaction_df['业务类型'] == '证券买卖']
    account_dict['成交额'] = credit_transaction_df['发生数量'].astype(float).mul(
        credit_transaction_df['成交价格'].astype(float)).sum()
    account_dict['成交额（含费）'] = abs(credit_transaction_df['发生金额'].astype(float)).sum()
    return account_dict


def read_matic_normal_account(path):
    # 读取华泰普通账户的资产信息
    # 文件名格式: 666810066802_衍舟弄潮2号_普通账单_HT1_20231120.xlsx
    account_df = pd.read_excel(path, sheet_name='资金情况', index_col=False, header=None)
    account_dict = {
        '账户净资产': get_value(account_df, '总资产'),
        '账户证券市值': get_value(account_df, '资产市值'),
        '资金余额': get_value(account_df, '资金余额'),
    }
    transaction_df = pd.read_excel(path, sheet_name='对账单', index_col=False, header=1)
    account_dict['成交额'] = abs(transaction_df.query('业务标志=="证券买入" or 业务标志=="证券卖出"')['成交金额']).sum()

    asset_df = pd.read_excel(path, sheet_name='持仓清单', index_col=False, header=1).dropna(how='any')
    asset_df['证券代码'] = asset_df['证券代码'].astype(int).astype(str)
    account_dict = update_asset(account_dict, asset_df, '证券代码', '证券名称', '参考市值')
    return account_dict


def read_matic_credit_account(path):
    # 读取华泰信用账户的资产信息
    # 文件名格式: 960000192208_衍舟弄潮2号_两融账单_HT1_20231120.xlsx
    account_df = pd.read_excel(path, sheet_name='资产负债情况', index_col=False, header=None)
    account_dict = {
        '账户净资产': get_value(account_df, '净资产'),
        '账户总资产': get_value(account_df, '总资产'),
        '账户证券市值': get_value(account_df, '证券市值'),
        '资金余额': get_value(account_df, '资金余额'),
    }

    basic_df = pd.read_excel(path, sheet_name='基本信息', index_col=False, header=None)
    account_dict['维担比例'] = get_value(basic_df, '维持担保比例', vertical=False)

    account_dict['账户总负债'] = account_dict['账户总资产'] - account_dict['账户净资产']

    transaction_df = pd.read_excel(path, sheet_name='业务流水', index_col=False, header=2)
    account_dict['成交额'] = abs(transaction_df.query('业务类型=="证券买卖"')['发生金额']).sum()

    #负债明细
    debt_df = pd.read_excel(path, sheet_name='负债情况', index_col=False, header=None)
    account_dict['融资负债'] = get_value(debt_df, '融资余额')
    account_dict['融券负债'] = get_value(debt_df, '融券市值')

    debt_df = sep_df(start='2、负债情况', df=debt_df)
    expense_cols = [col for col in debt_df.columns if '费用' in col or '利息' in col or col == '待扣收']
    account_dict['融资融券费用'] = debt_df.loc[:, expense_cols].sum().sum()


    #资产明细
    asset_df = pd.read_excel(path, sheet_name='当前资产', index_col=False, header=1).dropna(how='any')
    account_dict = update_asset(account_dict, asset_df, '证券代码', '证券简称', '当前市值')
    return account_dict

def update_asset(account_dict, asset_df, ticker_col, name_col, mark_val_col):
    num = len(asset_df)
    asset_df = get_instruments_type(asset_df, ticker_col)
    security_df = asset_df[asset_df['security type'] != 'Other']
    account_dict['账户证券市值'] = security_df[mark_val_col].astype(float).sum()
    ## 多头证券市值(不含现金类ETF)
    account_dict['多头证券市值(不含现金类ETF)'] = security_df[security_df[name_col]!='银华日利'][mark_val_col].astype(float).sum()
    ## 多头现金类市值(含现金类ETF,标准券)
    account_dict['多头现金类市值(含现金类ETF)'] = security_df[security_df[name_col] =='银华日利'][mark_val_col].astype(float).sum() + account_dict['资金余额'] + asset_df[asset_df[name_col]=='标准券'][mark_val_col].astype(float).sum()

    convertible = security_df[security_df['security type'] == 'Convertible'][mark_val_col].astype(
        float).sum()
    account_dict['可转债ETF市值'] = \
    security_df[(security_df['security type'] == 'ETF') & (security_df[name_col].str.contains('转债'))][mark_val_col].astype(float).sum() if num else 0
    ## 可转债市值(含可转债ETF)
    account_dict['可转债市值(含可转债ETF)'] = convertible + account_dict['可转债ETF市值']
    return account_dict



def get_value(df, key, vertical=True):
    if vertical:
        return df.iloc[np.where(df.values == key)[0][0] + 1,
        np.where(df.values == key)[1][0]]
    else:
        return df.iloc[np.where(df.values == key)[0][0],
        np.where(df.values == key)[1][0] + 1]


def sep_df(start, end=None, df=None):
    loc_start = np.where(df.values == start)[0][0] + 1
    loc_end = None if end is None else np.where(df.values == end)[0][0]
    new_df = df.iloc[loc_start:loc_end].dropna(axis=1, how='all')
    new_df.columns = new_df.iloc[0]
    return new_df.iloc[1:].dropna(how='any')


def get_instruments_type(df, col_name):
    rq.init()
    stock = rq.all_instruments(type='CS')['order_book_id'].str.split('.', expand=True)[0].tolist()
    etf = rq.all_instruments(type='ETF')['order_book_id'].str.split('.', expand=True)[0].tolist()
    convertible = rq.all_instruments(type='Convertible')['order_book_id'].str.split('.', expand=True)[0].tolist()
    df['security type'] = df[col_name].apply(
        lambda x: 'CS' if x in stock else 'ETF' if x in etf else 'Convertible' if x in convertible else 'Other')
    return df


