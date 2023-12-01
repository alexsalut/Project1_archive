# -*- coding: utf-8 -*-
# @Time    : 2023/7/10 9:03
# @Author  : Youwei Wu, Suying Zhou
# @File    : daily_update.py
# @Software: PyCharm

import time
import pandas as pd

from EmQuantAPI import c

from util.send_email import Mail, R
from util.file_location import FileLocation as FL


def download_check_kc50_composition(date=None):
    date = time.strftime('%Y%m%d') if date is None else date
    save_path = rf'{FL().kc50_composition_dir}\{date}.csv'
    c_download_kc50_composition(date, save_path)
    kc50_composition = pd.read_csv(save_path)
    if len(kc50_composition) == 50:
        print('[kc50 composition] no error found, downloaded successfully')
        subject = f'[kc50 composition] downloaded successfully'
        content = f"""
        <table width="800" border="0" cellspacing="0" cellpadding="4">
        <tr>
        <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>KC50 composition has been generated</b></td>
        </tr>
        <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
        <p>Download path:</p>
        {save_path}
        """
        Mail().send(subject=subject, body_content=content, receivers=R.department['research'])
    else:
        print('[kc50 composition] Stock number not correct, retry downloading in five mins')
        Mail().send(subject='[Alert! kc 50 composition not correct]',
                    body_content=f"""
                    <table width="800" border="0" cellspacing="0" cellpadding="4">
                    <tr>
                    <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>Alert KC50 Composition</b></td>
                    </tr>
                    <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
                    <p>file path:</p> 
                    {save_path}
                    """,
                    receivers=R.department['research'][0]
                    )
        time.sleep(300)
        download_check_kc50_composition(date)


def c_download_kc50_composition(date, save_path):
    c.start("ForceLogin=1")
    df = c.sector("009007673", date, options='ispandas=1')['SECUCODE']
    c.stop()
    df.to_csv(save_path, index=False)
    print(f'[kc50 composition] {date} file has downloaded.')
