#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2024/5/6 13:05
# @Author  : Suying
# @Site    : 
# @File    : download_cap.py
import time

from EmQuantAPI import c
from util.send_email import Mail, R



def download_cap(date=None):
    date = time.strftime('%Y%m%d') if date is None else date
    print('download cap:', date)
    c.start()
    all_hs_stocks = c.sector("001004", tradedate=date).Codes  # 沪深A股
    df = c.csd(
        codes=all_hs_stocks,
        indicators="MV,LIQMV",
        startdate=date,
        enddate=date,
        options="ispandas=1",
    )
    save_path = rf'\\192.168.1.116\data\cap/{date}.csv'
    df.to_csv(save_path)
    c.stop()

    subject = f'[市值数据{date}]下载完成'
    content = f"""
        <table width="800" border="0" cellspacing="0" cellpadding="4">
        <tr>
        <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>市值数据</b></td>
        </tr>
        <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
        <p><b>文件路径:</b></p>
        &nbsp&nbsp {save_path}
        """
    Mail().send(subject=subject, body_content=content, receivers=R.department['research'])


if __name__ == '__main__':
    download_cap('20240430')