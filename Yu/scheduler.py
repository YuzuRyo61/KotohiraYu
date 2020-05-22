import time
import sys

import schedule

from Yu.YuChan import timeReport, toot_memo, meow_time
from Yu.Util import PANIC
from Yu import log

def run_scheduler():
    # スケジュール一覧
    schedule.every().minute.at(":00").do(timeReport)
    schedule.every().minute.at(":55").do(toot_memo)
    schedule.every().day.at("22:22").do(meow_time)

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    except:
        PANIC(sys.exc_info())
        log.logErr("＊５秒後にスケジュールを再起動しますっ！")
        time.sleep(5)
        run_scheduler()
