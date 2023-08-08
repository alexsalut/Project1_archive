from apscheduler.schedulers.blocking import BlockingScheduler
import datetime
import time

def check_update_needed():
    current_time = datetime.datetime.now().time()
    update_time = datetime.time(14, 0, 0)

    if current_time < update_time:
        return True

    else：
        return False
