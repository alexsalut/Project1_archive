#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/25 11:29
# @Author  : Suying
# @Site    : 
# @File    : remote_recorder.py

import time

import xlwings as xw


def update_account_remote(account_path, remote_account_path):
    try:
        app = xw.App(visible=False, add_book=False)
        wb = xw.books.open(account_path)
        wb.save(remote_account_path)
        wb.close()
        app.quit()
        print(f'{remote_account_path} remote updating finished')
    except Exception as e:
        print(e)
        print(f'{account_path} remote updating failed, retry in 10 seconds')
        time.sleep(10)
        update_account_remote(account_path, remote_account_path)