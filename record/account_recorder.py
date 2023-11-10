import time
import xlwings as xw
import os
from file_location import FileLocation as FL
from record.cnn_recorder import Cnn_Recorder
from record.talang_recorder import TalangRecorder
from record.panlan1_tinglian2_recorder import PanlanTinglianRecorder
from record.remote_recorder import update_account_remote
from record.nongchao_recorder import NongchaoRecorder
from util.send_email import Mail, R
from util.trading_calendar import TradingCalendar as TC

def account_recorder(date=None, adjust=None):
    formatted_date = date if date is not None else time.strftime('%Y%m%d')
    last_trading_day = TC().get_n_trading_day(formatted_date,-1).strftime('%Y%m%d')
    old_account_path = rf'{FL().monitor_dir}\衍舟策略观察_{last_trading_day}.xlsx'
    today_account_path = rf'{FL().monitor_dir}\衍舟策略观察_{formatted_date}.xlsx'
    monitor_path = rf'{FL().monitor_dir}\monitor_{formatted_date}.xlsx'
    remote_account_path = rf'{FL().remote_monitor_dir}\衍舟策略观察.xlsx'

    if adjust is None:
        account_path = today_account_path
        date_to_update = formatted_date
        copy_cnn_account(account_path=old_account_path, save_path=today_account_path)
        Cnn_Recorder(account_path=account_path, monitor_path=monitor_path, date=date).cnn_recorder()
    else:
        account_path = old_account_path
        date_to_update = last_trading_day

    TalangRecorder(account_path=account_path, date=date_to_update, adjust=adjust).record_talang()
    PanlanTinglianRecorder(account_path=account_path, account='panlan1', date=date_to_update, adjust=adjust).record_account()
    PanlanTinglianRecorder(account_path=account_path, account='tinglian2', date=date_to_update, adjust=adjust).record_account()
    NongchaoRecorder(account_path=account_path, date=date_to_update, adjust=adjust).record_nongchao()
    update_account_remote(account_path=account_path, remote_account_path=remote_account_path)

    # os.remove(old_account_path)
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
        {remote_account_path}
        <p><b>更新内容:</b></p>
        <p>更新踏浪1号、踏浪2号、踏浪3号、盼澜1号、听涟2号的资产信息</p>
        """,
        receivers=R.department['research']
    )

def copy_cnn_account(account_path, save_path):
    app = xw.App(visible=False, add_book=False)
    wb = app.books.open(account_path)
    wb.save(save_path)
    wb.close()
    app.quit()
    print(f'Copy {account_path} to {save_path} successfully')

if __name__ == '__main__':
    account_recorder()

