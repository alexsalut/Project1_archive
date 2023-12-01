#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/29 9:56
# @Author  : Suying
# @Site    : 
# @File    : rzrq_limit.py
import os.path
import time

from util.send_email import Mail,R


def download_rzrq_limit_file(date=None):
    date = time.strftime('%Y%m%d') if date is None else date
    dir = r'\\192.168.1.116\trade\broker\rzrq'
    file_name = rf'融资融券标的 {date}.csv'
    Mail().receive(save_dir=dir, file_list=[file_name])
    if os.path.exists(rf'{dir}\{file_name}'):
        print(f'[融资融券标的文件]{file_name}下载成功')
    else:
        print(f'[融资融券标的文件]{file_name}下载失败, 10分钟后重试')
        Mail().send(
            subject=f'[融资融券标的文件]{file_name}下载失败, 10分钟后重试',
            body_content=f'[融资融券标的文件]{file_name}下载失败, 10分钟后重试',
            receivers=R.staff['zhou']
        )
        time.sleep(600)
        download_rzrq_limit_file(date=date)

