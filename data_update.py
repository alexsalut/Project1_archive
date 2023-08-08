import datetime

from st_list_daily_update import st_list_update
from kc50_weight_update import kc50_weight_update
from apscheduler.schedulers.blocking import BlockingScheduler


def update():
    scheduler = BlockingScheduler()
    scheduler.add_job(st_list_update, 'cron', hour=14, minute=0)
    scheduler.add_job(kc50_weight_update, 'cron', hour=14, minute=10)
    scheduler.start()


def update_schedule():
    current_time = datetime.datetime.now()
    if current_time.hour < 12 or current_time.hour > 15:
        print("Now is not trading time, no need to update")
        return

    if current_time.weekday() in [5, 6]:
        print("Today is weekend, no need to update")
        return

    kc50_weight_update()
    st_list_update()








