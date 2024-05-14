#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/11/29 9:56
# @Author  : Suying
# @Site    : 
# @File    : rzrq_limit.py
import glob
import os.path
import time

import pandas as pd

from util.send_email import Mail, R


def download_rzrq_limit_file(date=None):
    date = time.strftime('%Y%m%d') if date is None else date
    rq_dir = r'\\192.168.1.116\trade\broker\rzrq'
    rq_file_name = rf'融资融券标的 {date}.csv'
    Mail().receive(save_dir=rq_dir, date_range=[2, 2], file_list=[rq_file_name])

    if os.path.exists(rf'{rq_dir}\{rq_file_name}'):
        print(f'[融资融券标的文件]{rq_dir}\{rq_file_name}下载成功')
        Mail().send(
            subject=f'[融资融券标的文件]{rq_file_name}下载成功',
            body_content=f'[融资融券标的文件]{rq_dir}\{rq_file_name}下载成功',
            receivers=R.department['research']
        )
    else:
        print(f'!!![融资融券标的文件]{rq_dir}\{rq_file_name}下载失败, 10分钟后重试')
        Mail().send(
            subject=f'!!!!![融资融券标的文件]{rq_file_name}还未发送到指定邮箱, 10分钟后重试',
            body_content=f'[融资融券标的文件]{rq_file_name}还未发送到指定邮箱, 10分钟后重试',
            receivers=R.department['research']
        )
        time.sleep(600)
        download_rzrq_limit_file(date=date)


def download_citic_rq_file(date=None):
    date1 = time.strftime('%Y%m%d') if date is None else date
    date2 = pd.to_datetime(date1).strftime('%Y-%m-%d')
    rq_dir = r'D:\data\中信券源\raw'
    rq_file_name1 = rf'CITIC_SBL_Securities_List{date1}'
    rq_file_name2 = rf'CITIC_SBL_Securities_List{date2}'
    Mail().receive(save_dir=rq_dir, date_range=[4, 2], file_list=[rq_file_name1, rq_file_name2])

    files = glob.glob(rf'{rq_dir}\CITIC_SBL_Securities_List*.xlsx')
    file = [file for file in files if date1 in file or date2 in file]
    if len(file) != 0:
        file_path = file[0]
        print(f'[中信融资融券标的文件]{file_path}下载成功')
        Mail().send(
            subject=f'[中信融资融券标的文件]{file_path}下载成功',
            body_content=f'[中信融资融券标的文件]{file_path}下载成功',
            receivers=R.staff['zhou']
        )
    else:
        print(f'[中信融资融券标的文件]{rq_file_name1}下载失败, 10分钟后重试')
        Mail().send(
            subject=f'[中信融资融券标的文件]{rq_file_name1}还未发送到指定邮箱, 10分钟后重试',
            body_content=f'[中信融资融券标的文件]{rq_file_name1}还未发送到指定邮箱, 10分钟后重试',
            receivers=R.staff['zhou']
        )
        time.sleep(600)
        download_citic_rq_file(date=date1)





def check_rzrq_limit_file(date=None):
    date = time.strftime('%Y%m%d') if date is None else date
    file_name = rf'融资融券标的 {date}.csv'
    dir = r'\\192.168.1.116\trade\broker\rzrq'
    Mail().receive(save_dir=dir, date_range=[2, 2], file_list=[file_name])

    if not os.path.exists(rf'{dir}\{file_name}'):
        print(f'[融资融券标的文件]{file_name}下载失败, 10分钟后重试')
        Mail().send(
            subject=f'[融资融券标的文件]{file_name}还未发送到指定邮箱, 10分钟后重试',
            body_content=f'[融资融券标的文件]{file_name}还未发送到指定邮箱, 10分钟后重试',
            receivers=R.department['research']
        )
        time.sleep(600)
        download_rzrq_limit_file(date=date)


if __name__ == '__main__':
    # download_citic_rq_file()
    download_rzrq_limit_file()