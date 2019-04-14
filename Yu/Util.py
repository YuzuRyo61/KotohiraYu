# -*- coding: utf-8 -*-

import datetime
from pytz import timezone
from bs4 import BeautifulSoup
import traceback
import os
from time import sleep

class KotohiraUtil:
    @staticmethod
    def PANIC():
        # raiseされたら実行する。別途スクリプトで例外処理する必要がある
        now = datetime.datetime.now(timezone('Asia/Tokyo'))
        nowFormat = now.strftime("%Y/%m/%d %H:%M:%S")
        nowFileFormat = now.strftime("%Y%m%d")
        os.makedirs('panic-log', exist_ok=True)
        with open(f'panic-log/PANIC-{nowFileFormat}.TXT', 'a') as f:
            f.write('--- PANIC! {} ---\n'.format(nowFormat))
            traceback.print_exc(file=f)
            f.write('\n')
        print("＊ユウちゃんパニックですぅ・・・！\n{}".format(traceback.format_exc()))

    @staticmethod
    def h2t(txt):
        return BeautifulSoup(txt, features='html.parser').get_text()
    
    @staticmethod
    def schedule(func, doTimeList):
        # 指定した時間帯に実施する関数
        print(f"Setting feature: {func} at {doTimeList}")
        try:
            while True:
                now = datetime.datetime.now(timezone('Asia/Tokyo'))
                nowH = now.strftime("%H")
                nowM = now.strftime("%M")
                for time in doTimeList:
                    if len(time.split(":")) == 2:
                        h, m = time.split(":")
                        if (h == nowH or h == '**' or h == '*') and m == nowM:
                            print(f"指定した時間になったので実行っ！：{func}")
                            func()
                            sleep(60)
                    else:
                        sleep(10)
        except:
            KotohiraUtil.PANIC()
            print('五秒待って読み込みし直しますねっ！')
            sleep(5)
            KotohiraUtil.schedule(func, doTimeList)