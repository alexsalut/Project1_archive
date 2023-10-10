#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/22 16:58
# @Author  : Suying
# @Site    : 
# @File    : account_position.py
import time

import pandas as pd
from util.utils import send_email, SendEmailInfo
from account_position.panlan1_positon import Panlan1Position as pp
from account_position.tinglian2_position import Tinglian2Position as tl2
from account_position.talang1_position import Talang1Position as tl1

def check_notify_position(date=None):
    formatted_date = time.strftime('%Y%m%d') if date is None else pd.to_datetime(date).strftime("%Y%m%d")
    panlan1_dict = check_account_pos(
        actual_pos_df=pp(formatted_date).get_panlan1_actual_position(),
        target_pos_df=pp(formatted_date).get_panlan1_target_position()
    )
    tinglian2_dict = check_account_pos(
        actual_pos_df=tl2(formatted_date).get_tinglian2_actual_position(),
        target_pos_df=tl2(formatted_date).get_tinglian2_target_position()
    )
    talang1_dict = check_account_pos(
        actual_pos_df=tl1(formatted_date).get_talang1_actual_position(),
        target_pos_df=tl1(formatted_date).get_talang1_target_position()
    )
    subject = f'[Position Check] PositionCheck-{formatted_date}'
    content = f"""
    <table width="800" border="0" cellspacing="0" cellpadding="4">
    <tr>
    <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>踏浪1号|盼澜1号|听涟2号 持仓核对结果</b></td>
    </tr>
    <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
    <p>踏浪1号实际持仓文件路径：</p>
    &nbsp&nbsp{tl1(formatted_date).talang1_actual_pos_path}
    <p>踏浪1号目标持仓文件路径：</p>
    &nbsp&nbsp{tl1(formatted_date).talang1_target_pos_path}
    <p>踏浪1号实际持仓市值：</p>
    &nbsp&nbsp<font color=red>{talang1_dict['market val total']:.1f}</font>
    <p><b>踏浪1号持仓核对结果：</b></p>
    <center>{talang1_dict['pos df']}</center>
    
    <p>盼澜1号实际持仓文件路径：</p>
    &nbsp&nbsp{pp(formatted_date).panlan1_actual_pos_path}
    <p>盼澜1号目标持仓文件路径：</p>
    &nbsp&nbsp{pp(formatted_date).panlan1_target_pos_path}
    <p>盼澜1号实际持仓参考市值：</p>
    &nbsp&nbsp<font color=red>{panlan1_dict['market val total']:.1f}</font>
    <p><b>盼澜1号持仓核对结果：</b></p>
    <center>{panlan1_dict['pos df']}</center>

    <p>听涟2号实际持仓文件路径：</p>
    &nbsp&nbsp{tl2(formatted_date).tinglian2_actual_pos_path}
    <p>听涟2号目标持仓文件路径：</p>
    &nbsp&nbsp{tl2(formatted_date).tinglian2_target_pos_path}
    <p>听涟2号实际持仓市值：</p>
    &nbsp&nbsp<font color=red>{tinglian2_dict['market val total']:.1f}</font>
    <p><b>听涟2号持仓核对结果：</b></p>
    <center>{tinglian2_dict['pos df']}</center>
    """

    print(content)
    send_email(subject, content,
               receiver=SendEmailInfo.department['research'] + SendEmailInfo.department['tech'])


def check_account_pos(actual_pos_df, target_pos_df):
    pos_df = actual_pos_df.merge(target_pos_df, how='outer', left_index=True, right_index=True)
    pos_df['实际-目标'] = pos_df['实际'] - pos_df['目标']
    pos_df['偏移比率%'] = (100 * (pos_df['实际'] - pos_df['目标']) / pos_df['目标']).round(1)
    pos_df = pos_df.sort_values(by='市值', ascending=False)[['名称', '实际', '目标', '实际-目标', '偏移比率%', '市值']]
    market_val_total = pos_df['市值'].sum().round(2)
    pos_df['市值'] = pos_df['市值'].astype('int64', errors='ignore')

    def highlight_diff(s):
        if s != 0:
            return f'background-color: red'
        else:
            return ''

    styled_pos_df = pos_df.reset_index(drop=False).style.applymap(highlight_diff, subset=['实际-目标','偏移比率%'])
    styled_pos_df = styled_pos_df.format({'实际': '{:.0f}', '目标': '{:.0f}', '实际-目标': '{:.0f}', '偏移比率%': '{:.1f}'})
    styled_pos_df = styled_pos_df.to_html(classes='table', escape=False)
    styled_pos_df = styled_pos_df.replace('<table', '<table style="border-collapse: collapse; border: 1px solid black;"')
    styled_pos_df = styled_pos_df.replace('<tr', '<tr style="border-bottom: 1px solid black;"')
    styled_pos_df = styled_pos_df.replace('<th', '<th style="border-right: 1px solid black;"')
    styled_pos_df = styled_pos_df.replace('<td', '<td style="border-right: 1px solid black;"')

    pos_dict = {
        'pos df': styled_pos_df,
        'market val total': market_val_total
    }
    return pos_dict


if __name__ == '__main__':
    check_notify_position()
