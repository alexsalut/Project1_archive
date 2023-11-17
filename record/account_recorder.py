import time
import shutil

from util.file_location import FileLocation
from record.multi_strategy_perf import MultiStrategyPerf
from record.talang_recorder import TalangRecorder
from record.panlan1_tinglian2_recorder import PanlanTinglianRecorder
from record.nongchao_recorder import NongchaoRecorder
from util.send_email import Mail, R
from util.trading_calendar import TradingCalendar


def account_recorder(date=None, adjust=None):
    seq = '*' * 50
    print(f"\n{seq} Update Account Recorder {seq}")

    formatted_date = time.strftime('%Y%m%d') if date is None else date
    last_trading_day = TradingCalendar().get_n_trading_day(formatted_date, -1).strftime('%Y%m%d')

    monitor_dir = FileLocation.remote_monitor_dir
    old_account_path = rf'{monitor_dir}\衍舟策略观察_{last_trading_day}.xlsx'
    account_path = rf'{monitor_dir}\衍舟策略观察_{formatted_date}.xlsx'
    monitor_path = rf'{monitor_dir}\monitor_{formatted_date}.xlsx'

    if adjust is None:
        date_to_update = formatted_date
        print(f'Copy \n  {old_account_path}\nto\n  {account_path}')
        shutil.copyfile(src=old_account_path, dst=account_path)
        MultiStrategyPerf(
            account_path=account_path,
            monitor_path=monitor_path,
            date=date,
        ).update()
    else:
        account_path = old_account_path
        date_to_update = last_trading_day

    update_fund_recorder(account_path, date_to_update, adjust)
    send_email(account_path, date_to_update)


def update_fund_recorder(account_path, date_to_update, adjust):
    TalangRecorder(account_path=account_path, date=date_to_update, adjust=adjust).update()
    NongchaoRecorder(account_path=account_path, date=date_to_update, adjust=adjust).record_nongchao()
    # PanlanTinglian这里有问题，亮哥程序只生成一个excel pid并且不会quit掉
    PanlanTinglianRecorder(account_path=account_path, account='盼澜1号', date=date_to_update, adjust=adjust).record_account()
    PanlanTinglianRecorder(account_path=account_path, account='听涟2号', date=date_to_update, adjust=adjust).record_account()


    
def send_email(account_path, date_to_update):
    content = f"""
        <table width="800" border="0" cellspacing="0" cellpadding="4">
        <tr>
        <td bgcolor="#CECFAD" height="30" style="font-size:21px"><b>CNN 策略观察</b></td>
        </tr>
        <td bgcolor="#EFEBDE" height="100" style="font-size:13px">
        <p><b>文件路径:</b></p>
        {account_path}
        <p><b>更新内容:</b></p>
        <p>更新踏浪1号、踏浪2号、踏浪3号、盼澜1号、听涟2号的资产信息</p>
        """
    Mail().send(
        subject=f'[衍舟策略观察] {date_to_update} 更新完成',
        body_content=content,
        receivers=R.department['research'] + R.department['admin'],
    )


if __name__ == '__main__':
    account_recorder(date='20231116')
