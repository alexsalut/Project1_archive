#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/10/20 13:47
# @Author  : Suying
# @Site    : 
# @File    : mini_strategy.py
import glob
import os

import pandas as pd

from file_location import FileLocation
def get_mini_strategy_history_ret(start):
    dir = FileLocation.monitor_dir
    filepath_list = glob.glob(os.path.join(dir, 'monitor_*.xlsx'))
    filepath_list = [path for path in filepath_list if 'formula' not in path]

    ret = []
    for path in filepath_list:
        date = os.path.basename(path).split('.')[0].split('_')[1]
        if date >= start:
            df = pd.read_excel(path, sheet_name='monitor目标持仓', index_col=0, header=2)
            df = df.query('index.notnull()').iloc[:5,:]
            ret_dict = {index : df.loc[index, '超额收益'] for index in df.index}
            # ret_dict.update({index : df.loc[index, '超额收益'] for index in df.index})
            ret_dict.update({'date': date})
            ret.append(ret_dict)
    ret_df = pd.DataFrame(ret).set_index('date')
    ret_df.to_csv(os.path.join(dir, 'mini_strategy_history_ret.csv'))



if __name__ == '__main__':
    get_mini_strategy_history_ret('20231018')