import time
import xlwings as xw
import os
from file_location import FileLocation as FL
from account_record.cnn_recorder import Cnn_Recorder
from account_record.talang_recorder import TalangRecorder
from account_record.panlan1_recorder import Panlan1Recorder
from account_record.remote_recorder import update_account_remote
from util.utils import send_email, SendEmailInfo
from util.trading_calendar import TradingCalendar as TC

def account_recorder(date=None):
    formatted_date = date if date is not None else time.strftime('%Y%m%d')
    last_trading_day = TC().get_n_trading_day(formatted_date,-1).strftime('%Y%m%d')
    old_account_path = rf'{FL().monitor_dir}\cnn策略观察_{last_trading_day}.xlsx'
    today_account_path = rf'{FL().monitor_dir}\cnn策略观察_{formatted_date}.xlsx'
    monitor_path = rf'{FL().monitor_dir}\monitor_{formatted_date}.xlsx'
    remote_account_path = rf'{FL().remote_monitor_dir}\cnn策略观察.xlsx'

    copy_cnn_account(account_path=old_account_path, save_path=today_account_path)
    Cnn_Recorder(account_path=today_account_path, monitor_path=monitor_path, date=date).cnn_recorder()
    TalangRecorder(account_path=today_account_path, date=date).record_talang()
    Panlan1Recorder(account_path=today_account_path, date=date).record_panlan1()
    update_account_remote(account_path=today_account_path, remote_account_path=remote_account_path)
    os.remove(old_account_path)
    send_email(
        subject=f'[CNN 策略观察] {formatted_date} 更新完成',
        content=f"""
        <table width="800" border="0" cellspacing="0" cellpadding="4">
        <tr>
        <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>CNN 策略观察</b></td>
        </tr>
        <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
        <p><b>文件路径:</b></p>
        {today_account_path}
        {remote_account_path}
        <p><b>更新内容:</b></p>
        单策略超额
        多策略超额
        踏浪2号
        踏浪3号
        盼澜1号
        """,
        receiver=SendEmailInfo.department['research']
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

