# -*- coding: utf-8 -*-

from datetime import datetime
from pytz import timezone
from bs4 import BeautifulSoup
import traceback
import os

class KotohiraUtil:
    @staticmethod
    def PANIC():
        now = datetime.now(timezone('Asia/Tokyo'))
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