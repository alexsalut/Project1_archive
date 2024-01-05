#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/12/20 9:58
# @Author  : Suying
# @Site    : 
# @File    : fee_analysis.py
import pandas as pd

def get_fee_composition(path, name, type_col, vol_col, commission_col, tax_col, transfer_fee_col):
    df = pd.read_excel(path, index_col=0, header=0)
    fee_df = df.groupby(type_col)[[vol_col, commission_col, tax_col, transfer_fee_col]].sum()

    for n in [vol_col, commission_col, tax_col, transfer_fee_col]:
        fee_df[n+'率'] = 100 * abs(fee_df[n] / fee_df[vol_col])
    fee_df.to_csv(f'{name}_3费率.csv', encoding='utf-8-sig')

if __name__ == '__main__':

    type_col = '摘要代码'
    vol_col = '发生金额'
    commission_col = '佣金'
    tax_col = '印花税'
    transfer_fee_col = '过户费'
    dir = r'C:\Users\Yz02\Desktop\Data\Save\费率'
    name = ['盼澜1号-普通', '盼澜1号-信用','踏浪1号-普通', '踏浪信用2']


    i = 3
    get_fee_composition(f'{dir}/{name[i]}.xlsx', name[i], type_col, vol_col, commission_col, tax_col, transfer_fee_col)


