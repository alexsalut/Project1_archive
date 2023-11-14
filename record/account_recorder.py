import time
import shutil

import xlwings as xw

from file_location import FileLocation as FL
from record.cnn_recorder import Cnn_Recorder
from record.talang_recorder import TalangRecorder
from record.panlan1_tinglian2_recorder import PanlanTinglianRecorder
from record.remote_recorder import update_account_remote
from record.nongchao_recorder import NongchaoRecorder
from util.send_email import Mail, R
from util.trading_calendar import TradingCalendar


def account_recorder(date=None, adjust=None):
    formatted_date = date if date is not None else time.strftime('%Y%m%d')
    last_trading_day = TradingCalendar().get_n_trading_day(formatted_date, -1).strftime('%Y%m%d')
    old_account_path = rf'{FL.remote_monitor_dir}\衍舟策略观察_{last_trading_day}.xlsx'
    today_account_path = rf'{FL.remote_monitor_dir}\衍舟策略观察_{formatted_date}.xlsx'
    monitor_path = rf'{FL.remote_monitor_dir}\monitor_{formatted_date}.xlsx'
    # remote_account_path = rf'{FL.remote_monitor_dir}\衍舟策略观察.xlsx'

    if adjust is None:
        account_path = today_account_path
        date_to_update = formatted_date
        print('copy_cnn_account...')
        shutil.copyfile(src=old_account_path, dst=today_account_path)
        print('cnn_recorder...')
        Cnn_Recorder(account_path=account_path, monitor_path=monitor_path, date=date).cnn_recorder()
    else:
        account_path = old_account_path
        date_to_update = last_trading_day

    print('talang')
    TalangRecorder(account_path=account_path, date=date_to_update, adjust=adjust).record_talang()
    print('panlan')
    PanlanTinglianRecorder(account_path=account_path, account='panlan1', date=date_to_update, adjust=adjust).record_account()
    print('tinglian')
    PanlanTinglianRecorder(account_path=account_path, account='tinglian2', date=date_to_update, adjust=adjust).record_account()
    print('nongchao')
    NongchaoRecorder(account_path=account_path, date=date_to_update, adjust=adjust).record_nongchao()

    Mail().send(
        subject=f'[衍舟策略观察] {date_to_update} 更新完成',
        body_content=f"""
        <table width="800" border="0" cellspacing="0" cellpadding="4">
        <tr>
        <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>CNN 策略观察</b></td>
        </tr>
        <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
        <p><b>文件路径:</b></p>
        {account_path}
        <p><b>更新内容:</b></p>
        <p>更新踏浪1号、踏浪2号、踏浪3号、盼澜1号、听涟2号的资产信息</p>
        """,
        receivers=R.department['research']
    )


if __name__ == '__main__':
    account_recorder()
