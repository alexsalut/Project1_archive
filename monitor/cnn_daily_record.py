import time

from util.trading_calendar import TradingCalendar as TC
from util.utils import send_email, SendEmailInfo
from file_location import FileLocation as FL
from monitor.monitor_archive import archive_monitor_today
from monitor.monitor_next_trading_day import update_monitor_next_trading_day


class CnnDailyRecord:
    def __init__(self, today=None):
        # self.monitor_dir = r'C:\Users\Yz02\Desktop\strategy_update - 副本'
        # self.remote_monitor_dir = r'C:\Users\Yz02\Desktop\strategy_update - 副本 - 副本'
        self.monitor_dir = FL().monitor_dir
        self.remote_monitor_dir = FL().remote_monitor_dir
        self.today = time.strftime('%Y%m%d') if today is None else today
        self.monitor_path = rf'{self.monitor_dir}/monitor_{self.today}_formula.xlsx'
        self.remote_summary_dir = FL().remote_summary_dir
        self.next_trading_day = TC().get_n_trading_day(self.today, 1).strftime('%Y%m%d')

    def update_monitor(self):
        update_monitor_next_trading_day(
            date=self.today,
            monitor_path=self.monitor_path,
            remote_monitor_dir=self.remote_monitor_dir,
            monitor_dir=self.monitor_dir,
            remote_summary_dir=self.remote_summary_dir)
        send_email(
            subject=f'Monitor next trading day updated, archive today monitor in 100 seconds',
            content='',
            receiver=SendEmailInfo.department['research'][0]
        )
        time.sleep(100)
        archive_monitor_today(
            monitor_path=self.monitor_path,
            remote_monitor_dir=self.remote_monitor_dir,
            monitor_dir=self.monitor_dir,
            today=self.today
        )


if __name__ == '__main__':
    CnnDailyRecord().update_monitor()
