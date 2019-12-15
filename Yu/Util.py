import datetime
from pytz import timezone
from bs4 import BeautifulSoup
import traceback
import os
from time import sleep
import configparser
import requests

from mastodon import Mastodon

from Yu.config import config

mastodon = Mastodon(
    access_token='config/accesstoken.txt',
    api_base_url=config['instance']['address']
)

def PANIC(dbPanic=False):
    # raiseされたら実行する。別途スクリプトで例外処理する必要がある
    now = datetime.datetime.now(timezone('Asia/Tokyo'))
    nowFormat = now.strftime("%Y/%m/%d %H:%M:%S%z")
    nowFileFormat = now.strftime("%Y%m%d")
    os.makedirs('panic-log', exist_ok=True)
    with open(f'panic-log/PANIC-{nowFileFormat}.LOG', 'a', encoding="utf-8") as f:
        f.write('--- PANIC! {} ---\n'.format(nowFormat))
        traceback.print_exc(file=f)
        f.write('\n')
    print("＊ユウちゃんパニックですぅ・・・！\n{}".format(traceback.format_exc()))
    if config['linenotify']['enable'] == True and dbPanic == False:
        headers = {"Authorization": "Bearer " + config['linenotify']['token']}
        payload = {"message": "\n＊ユウちゃんがパニックになりました。\nパニック時刻: \n" + nowFormat + "\n詳細はログを確認してくださいっ"}
        if config['web']['enable']:
            payload['message'] += "\n" + config['web']['base'] + "/panic-log/" + nowFileFormat
        req = requests.post("https://notify-api.line.me/api/notify", headers=headers, params=payload)
        if req.status_code != 200:
            print("[FATAL] LINE NOTIFY ACCESS FAILED")
        else:
            print("LINET NOTIFY SENT")
    
    # パニックした時にトゥートできるか試しますっ！できなくてもエラーを出さないようにしますっ！
    if dbPanic == False:
        try:
            mastodon.toot("ユウちゃんパニックですぅ・・・！٩(ŏ﹏ŏ、)۶")
        except:
            pass

def h2t(txt):
    return BeautifulSoup(txt, features='html.parser').get_text()

def schedule(func, doTimeList):
    # 指定した時間帯に実施する関数。設定時間は24時間表記で設定する
    print(f"Setting feature: {func.__name__} at {doTimeList}")
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
        PANIC()
        print('五秒待って読み込みし直しますねっ！')
        sleep(5)
        schedule(func, doTimeList)
