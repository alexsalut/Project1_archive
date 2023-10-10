#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2023/9/22 16:58
# @Author  : Suying
# @Site    : 
# @File    : account_position.py

from util.utils import send_email, SendEmailInfo
from account_position.get_account_position import AccountPosition as ap
from account_position.account_location import get_account_location


def check_notify_position(date=None):
    account_list = ['talang1', 'panlan1', 'tinglian2']
    accunt_pos_dict = check_all_account_pos(account_list)
    subject = rf'[Position Check]PositionCheck {date}'
    content = gen_check_email_content(accunt_pos_dict)
    send_email(subject, content, SendEmailInfo.department['research'][0])  # + SendEmailInfo.department['tech'])


def check_all_account_pos(account_list, date=None):
    account_pos_dict = {}
    for account in account_list:
        account_pos_dict[account] = check_account_pos(ap(account, date).get_actual_position(),
                                                      ap(account, date).get_target_position())
    return account_pos_dict


def gen_check_email_content(account_pos_dict):
    account_loc_dict = get_account_location()
    content = f"""
    <table width="800" border="0" cellspacing="0" cellpadding="4">
    <tr>
    <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>踏浪1号|盼澜1号|听涟2号 持仓核对结果</b></td>
    </tr>
    <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
    """
    account_name_dict = {
        'panlan1': '盼澜1号',
        'tinglian2': '听涟2号',
        'talang1': '踏浪1号',
    }
    for account in account_pos_dict.keys():
        content += f"""
            <p>{account_name_dict[account]}实际持仓文件路径：</p>
            &nbsp&nbsp{account_loc_dict[account]['actual']}
            <p>{account_name_dict[account]}目标持仓文件路径：</p>
            &nbsp&nbsp{account_loc_dict[account]['target']}
            <p>{account_name_dict[account]}实际持仓市值：</p>
            &nbsp&nbsp<font color=red>{account_pos_dict[account]['market val total']:.1f}</font>
            <p><b>{account_name_dict[account]}持仓核对结果：</b></p>
            <center>{account_pos_dict[account]['pos df']}</center>
        """
    return content


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

    styled_pos_df = pos_df.reset_index(drop=False).style.applymap(highlight_diff, subset=['实际-目标', '偏移比率%'])
    styled_pos_df = styled_pos_df.format(
        {'实际': '{:.0f}', '目标': '{:.0f}', '实际-目标': '{:.0f}', '偏移比率%': '{:.1f}'})
    styled_pos_df = styled_pos_df.to_html(classes='table', escape=False)
    styled_pos_df = styled_pos_df.replace('<table',
                                          '<table style="border-collapse: collapse; border: 1px solid black;"')
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
