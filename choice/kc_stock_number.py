#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/25 10:09
# @Author  : Suying
# @Site    : 
# @File    : kc_stock_number.py
from EmQuantAPI import c
import pandas as pd

# 2023-09-25 10:21:57
# 科创板 成分个数
def get_kc_stock_num():
    c.start()
    num=c.cses("B_001057","SECTORCOUNT","TradeDate=2023-09-25,IsHistory=0").Data['B_001057'][0]
    c.stop()
    return num