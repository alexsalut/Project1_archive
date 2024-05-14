#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/4/25 15:44
# @Author  : Suying
# @Site    : 
# @File    : nongchao1_rongquan.py

import glob
import pandas as pd
import numpy as np

def get_all_rongquan_data():
    dir = r'C:\Users\Yz02\Desktop\Data\Save\账户对账单'
    files = glob.glob(dir + rf'/衍舟弄潮1号-融资融券账户对账单（含约定融资＆约定融券）-8009286755_*.xlsx')

    order_data = []
    debt_rq_data = []
    yuequan_data = []
    for file in files:
        df = pd.read_excel(file)

        yuequan_df = yuequan_analysis(df, file)
        if yuequan_df is not None:
            yuequan_data.append(yuequan_df)

        daily_rq_debt = daily_rongquan_debt(df, file)
        if daily_rq_debt is not None:
            debt_rq_data.append(daily_rq_debt)

        order_df = rq_transaction(df)
        if order_df is not None:
            order_data.append(order_df)
    all_order_df = pd.concat(order_data, axis=0).reset_index(drop=True)
    all_order_df.to_pickle(r'data\nongchao1_order_df.pkl')

    all_debt_df = pd.concat(debt_rq_data, axis=0).reset_index(drop=True)
    all_debt_df.to_pickle(r'data\nongchao1_debt_df.pkl')
    all_yuequan_df = pd.concat(yuequan_data, axis=0).reset_index(drop=True)
    all_yuequan_df.to_pickle(r'data\nongchao1_yuequan_df.pkl')





def rq_transaction(df):
    order_start = '三、业务流水(合并对账单)'
    if len(np.where(df.values==order_start)) > 0:
        order_df = sep_df(order_start, end='合计：', df=df, subset=['摘要代码'])
        rongquan = order_df[order_df['摘要代码'].str.contains('融券卖出')]
        huanquan = order_df[order_df['摘要代码'].str.contains('还券')]
        duohuan = order_df[order_df['摘要代码'].str.contains('多还')]
        interest = order_df[order_df['摘要代码'].str.contains('融券费用')]
        df = pd.concat([rongquan, huanquan, duohuan, interest], axis=0)
        return df
    else:
        return None






        # rongquan_sell = order_df[order_df['摘要代码'].str.contains('融券卖出')]
        # huanquan = order_df[order_df['摘要代码'].str.contains('还券')]


def daily_rongquan_debt(df, path):
    debt_start = '3、融资融券负债明细(合并对账单)'
    if len(np.where(df.values==debt_start)) > 0:
        debt_df = sep_df(debt_start, end='合计：', df=df, subset=['合约类型'])
        debt_rq_df = debt_df[debt_df['合约类型'] == '融券']
        debt_rq_df['记录日期'] = path.split('_')[-1].split('.')[0]
    else:
        debt_rq_df = None
    return debt_rq_df



def yuequan_analysis(df, path):
    yuequan_start = '4、约定融资|约定融券合约明细'
    if len(np.where(df.values==yuequan_start)) > 0:
        yuequan_df = sep_df(yuequan_start, end='合计：', df=df, subset=['证券代码'])
        yuequan_df['合约编号'] = yuequan_df['合约编号'].astype(str)
        yuequan_df['生效日期'] = yuequan_df['合约编号'].str[:8]
        yuequan_df['记录日期'] = path.split('_')[-1].split('.')[0]
        return yuequan_df
    else:
        return None


def sep_df(start, end=None, df=None, subset=None):
    loc_start = np.where(df.values == start)[0][0] + 1
    if end is not None:
        locs_end = sorted(np.where(df.values == end)[0])
        locs_end = [loc for loc in locs_end if loc > loc_start]
        if len(locs_end) > 0:
            loc_end = locs_end[0]
        else:
            loc_end = None
    else:
        loc_end = None
    new_df = df.iloc[loc_start:loc_end].dropna(how='all')
    new_df.columns = new_df.iloc[0]
    if subset is None:
        return new_df[subset].iloc[1:].dropna(how='any')
    else:
        return new_df.iloc[1:].dropna(subset=subset)




if __name__ == '__main__':
    get_all_rongquan_data()