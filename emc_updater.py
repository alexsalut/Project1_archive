import pandas as pd
import datetime
import os
import glob

from utils import send_email

def emc_updater():
    today = datetime.datetime.now().strftime('%Y%m%d')
    subject = f'[EMC update] emc position file check'
    save_dir = r'\\192.168.1.116\trade\broker\emc\account'

    position_6516_path = rf'{save_dir}/310300016516_POSITION.{today}.csv'
    position_0343_path = rf'{save_dir}/310310300343_RZRQ_POSITION.{today}.csv'


    position_6516_df = check_file(position_6516_path)
    position_6516_text = position_6516_df.to_string() if position_6516_df is not None else ''


    position_0343_df = check_file(position_0343_path)
    position_0343_text = position_0343_df.to_string() if position_0343_df is not None else ''

    content = f"""
    {position_6516_path}:
    {position_6516_text}
    
    {position_0343_path}:
    {position_0343_text}
    """
    print(subject)
    print(content)
    send_email(subject, content)


def check_file(file_path):
    file_name = os.path.basename(file_path)
    if os.path.exists(file_path):
        print(f'{file_name} exists.')
        df = pd.read_csv(file_path, encoding='gbk')
        filter_df = df.query('持仓数量 != 0').sort_values(by='市值', ascending=False).reset_index(drop=True)
        filter_df.style.set_properties(**{'text-align': 'right'})
        return filter_df
    else:
        print(f'{file_name} does not exist.')
        return None

if __name__ == '__main__':
    emc_updater()