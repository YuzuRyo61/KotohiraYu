import configparser
import datetime
import os
import sys
import traceback
from time import sleep

import requests
from bs4 import BeautifulSoup
from pytz import timezone

from Yu import log
from Yu.config import config
from Yu.mastodon import mastodon

def PANIC(exc_info):
    # raiseされたら実行する。別途スクリプトで例外処理する必要がある
    now = datetime.datetime.now(timezone('Asia/Tokyo'))
    nowFormat = now.strftime("%Y/%m/%d %H:%M:%S%z")
    nowFileFormat = now.strftime("%Y%m%d")
    os.makedirs('panic-log', exist_ok=True)
    with open(f'panic-log/PANIC-{nowFileFormat}.LOG', 'a', encoding="utf-8") as f:
        f.write('--- PANIC! {} ---\n'.format(nowFormat))
        traceback.print_exc(file=f)
        f.write('\n')
    log.logErr("＊ユウちゃんパニックですぅ・・・！\n{}".format(traceback.format_exc()))
    if config['linenotify']['enable'] == True:
        headers = {"Authorization": f"Bearer {config['linenotify']['token']}"}
        payload = {"message": f"\n＊ユウちゃんがパニックになりました。\nパニック時刻: \n{nowFormat}\nエラーメッセージ:\n{traceback.format_exception(*exc_info)[-1]}"}
        req = requests.post("https://notify-api.line.me/api/notify", headers=headers, params=payload)
        if req.status_code != 200:
            log.logErr("[FATAL] LINE NOTIFY ACCESS FAILED")
        else:
            log.logInfo("LINET NOTIFY SENT")
    
    # パニックした時にトゥートできるか試しますっ！できなくてもエラーを出さないようにしますっ！
    try:
        mastodon.toot("ユウちゃんパニックですぅ・・・！٩(ŏ﹏ŏ、)۶")
    except:
        pass

def h2t(txt):
    return BeautifulSoup(txt, features='html.parser').get_text()

def isVoteOptout(tags):
    if config['features']['voteOptout']:
        for tag in tags:
            if tag['name'] == config['features']['voteOptoutTag']:
                return True
        
    return False
