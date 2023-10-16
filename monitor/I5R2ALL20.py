#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/16 14:51
# @Author  : Suying
# @Site    : 
# @File    : I5R2ALL20.py
import glob
import os.path

import pandas as pd

if __name__ == '__main__':
    dir = r'C:\Users\Yz02\Desktop\strategy_update'
    file_list = glob.glob(f'{dir}/monitor_*.xlsx')
    filtered_list = [file for file in file_list if os.path.basename(file).split('.')[0].split('_')[1] >= '20230915']
    data = []
    for path in filtered_list:
        df = pd.read_excel(path, index_col='日期')
        df_filtered = df[df.index.notna()].iloc[2:7,7:9]
        df_filtered.columns = ['abs','excess']
        rank_df = df_filtered.rank(axis=0, ascending=False).T
        rank_df['date'] = os.path.basename(path).split('.')[0].split('_')[1]
        data.append(rank_df)
    all_rank_df = pd.concat(data, axis=0)
    print()








