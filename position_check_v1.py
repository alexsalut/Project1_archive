import pandas as pd
import datetime
import os
import time

from utils import send_email, SendEmailInfo

def position_check(date=None):
    today = datetime.datetime.now().strftime('%Y%m%d') if date is None else date
    subject = f'[Position Check] Product Position Check'
    tinglian_actual_pos_dir = r'\\192.168.1.116\trade\broker\emc\account'
    panlan1_actual_pos_dir = r'\\192.168.1.116\trade\broker\cats\account'
    target_pos_dir = r'\\192.168.1.116\trade\target_position\account'
    today_v1 = pd.to_datetime(today).strftime('%Y-%m-%d')

    actual_position_6516_path = rf'{panlan1_actual_pos_dir}/StockPosition_{today_v1}.csv'
    actual_position_0343_path = rf'{tinglian_actual_pos_dir}/310310300343_RZRQ_POSITION.{today}.csv'

    target_position_6516_path = rf'{target_pos_dir}/tag_pos_310300016516_{today}.csv'
    target_position_0343_path = rf'{target_pos_dir}/tag_pos_310310300343_RZRQ_{today}.csv'


    position_6516_df = check_panlan1_file(actual_position_6516_path, target_position_6516_path)
    position_6516_text = position_6516_df.to_string() if position_6516_df is not None else ''


    position_0343_df = check_tinglian_file(actual_position_0343_path, target_position_0343_path)
    position_0343_text = position_0343_df.to_string() if position_0343_df is not None else ''

    content = f"""
    actual position file path:{actual_position_6516_path}
    target position file path:{target_position_6516_path}\n
    {position_6516_text}
    
    actual position file path : {actual_position_0343_path}
    target position file path: {target_position_0343_path}\n
    {position_0343_text}
    """
    print(subject)
    print(content)
    send_email(subject, content, receiver=SendEmailInfo.department['research'] + [SendEmailInfo.department['tech'][1]])

def check_panlan1_file(actual_file_path, target_file_path):
    try:
        actual_df = pd.read_csv(actual_file_path).set_index('代码', drop=True)
        target_df = pd.read_csv(target_file_path)
        target_s = target_df.set_index(target_df.columns[0], drop=True).iloc[:,0]
        target_s.index = target_s.index.str[2:].astype(int)
        actual_s = actual_df['当前余额']
        merge_df = pd.concat([actual_s, target_s], axis=1, join='outer').fillna(0)
        merge_df = merge_df.rename(columns={merge_df.columns[0]:'实际',merge_df.columns[1]:'目标'})
        merge_df['实际'] = merge_df['实际'].astype(int)
        merge_df['目标'] = merge_df['目标'].astype(int)
        merge_df = merge_df[merge_df.sum(axis=1)!=0]
        merge_df['偏移比率%'] = 100*(merge_df['实际'] - merge_df['目标'])/merge_df['目标']
        merge_df['偏移比率%'] = merge_df['偏移比率%'].apply(lambda x: f'{x:.1f}')
        new_merge_df = pd.merge(actual_df['名称'], merge_df, left_index=True, right_index=True, how='right')
        return new_merge_df
    except Exception as e:
        print(e)
        check_tinglian_file(actual_file_path, target_file_path)

def check_tinglian_file(actual_file_path, target_file_path):
    file_name = os.path.basename(actual_file_path)
    try:
        actual_df = pd.read_csv(actual_file_path, encoding='gbk').rename(columns={'持仓数量':'实际持仓数量'})
        new_actual_df = actual_df.sort_values(by='市值', ascending=False).reset_index(drop=True)

        target_df = pd.read_csv(target_file_path, encoding='gbk')
        target_df = target_df.rename(columns={x:y for x,y in zip(target_df.columns, ['证券代码','目标持仓数量'])})
        target_df['证券代码'] = target_df['证券代码'].apply(lambda x: x[2:]).astype(int)

        merge_df = pd.merge(new_actual_df, target_df, on='证券代码', how='outer')
        merge_df.index = merge_df.index + 1
        merge_df = merge_df.rename(columns={
            '证券代码': '代码',
            '证券名称': '名称',
            '实际持仓数量': '实际',
            '目标持仓数量': '目标',
        })
        merge_df[['实际', '目标']] = merge_df[['实际', '目标']].fillna(0).astype(int)
        merge_df['偏移比率%'] = 100*(merge_df['实际'] - merge_df['目标'])/merge_df['目标']
        merge_df['偏移比率%'] = merge_df['偏移比率%'].apply(lambda x: f'{x:.1f}')
        check_df = merge_df[['代码','名称','实际','目标','偏移比率%']].copy()
        return check_df.query('实际!=0 or 目标!=0')
    except Exception as e:
        print(e)
        print(f'[EMC update] {file_name} access failed, retry in 10 seconds')
        time.sleep(10)
        check_tinglian_file(actual_file_path, target_file_path)

if __name__ == '__main__':
    position_check()




