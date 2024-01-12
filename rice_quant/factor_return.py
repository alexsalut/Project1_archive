#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/12/26 8:58
# @Author  : Suying
# @Site    : 
# @File    : factor_return.py


import rqdatac as rq


def get_factor_return(start_date, end_date, factor_name, universe='whole_market', method='implicit', model='v1'):
    rq.init()
    factor_return = rq.get_factor_return(start_date=start_date,
                                         end_date=end_date,
                                         factors=factor_name,
                                         universe=universe,
                                         method=method,
                                         model=model)
    factor_return.to_csv(rf'全A因子收益率(显式)_{start_date}_{end_date}.csv', encoding='utf_8_sig')
