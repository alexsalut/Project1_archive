#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/4/25 16:54
# @Author  : Suying
# @Site    : 
# @File    : nongchao2_rongquan.py



import glob
import pandas as pd

def get_all_rongquan_data():
    dir = r'C:\Users\Yz02\Desktop\Data\Save\账户对账单'
    files = glob.glob(dir + rf'/960000192208_衍舟弄潮2号_两融账单_HT1_*.xlsx')

    order_data = []
    debt_rq_data = []
    yuequan_data = []
    for file in files:
        yuequan_df = yuequan_analysis(file)
        if yuequan_df is not None:
            yuequan_data.append(yuequan_df)

        daily_rq_debt = daily_rongquan_debt(file)
        if daily_rq_debt is not None:
            debt_rq_data.append(daily_rq_debt)

        order_df = rq_transaction(file)
        if order_df is not None:
            order_data.append(order_df)

    all_order_df = pd.concat(order_data, axis=0).reset_index(drop=True)
    all_order_df.to_pickle(r'data\nongchao2_order_df.pkl')

    all_debt_df = pd.concat(debt_rq_data, axis=0).reset_index(drop=True)
    all_debt_df.to_pickle(r'data\nongchao2_debt_df.pkl')
    all_yuequan_df = pd.concat(yuequan_data, axis=0).reset_index(drop=True)
    all_yuequan_df.to_pickle(r'data\nongchao2_yuequan_df.pkl')



def rq_transaction(file):
    order_df = pd.read_excel(file, sheet_name='业务流水', header=2, index_col=False)
    order_df = order_df.dropna(subset=['摘要代码'])
    order_df['摘要代码'] = order_df['摘要代码'].astype(str)

    rongquan = order_df[order_df['摘要代码'].str.contains('融券卖出')]

    huanquan = order_df[order_df['摘要代码'].str.contains('还券')]
    duohuan = order_df[order_df['摘要代码'].str.contains('多还')]
    interest = order_df[order_df['摘要代码'].str.contains('融券费用')]
    df = pd.concat([rongquan, huanquan, duohuan, interest], axis=0)
    return df



def daily_rongquan_debt(file):
    df = pd.read_excel(file, sheet_name='负债明细', header=2, index_col=False)
    df = df.dropna(subset=['证券代码'])
    if len(df) > 0:
        date = file.split('_')[-1].split('.')[0]
        df['记录日期'] = date
        return df
    else:
        return None


def yuequan_analysis(file):
    df = pd.read_excel(file, sheet_name='资券头寸合约信息', header=2, index_col=False)
    df = df.dropna(subset=['证券代码'])
    if len(df) > 0:
        date = file.split('_')[-1].split('.')[0]
        df['头寸合约编号'] = df['头寸合约编号'].astype(str)
        df['生效日期'] = df['头寸合约编号'].str[:8]
        df['记录日期'] = date
        return df
    else:
        return None



if __name__ == '__main__':
    get_all_rongquan_data()