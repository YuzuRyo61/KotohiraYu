# -*- coding: utf-8 -*-

import datetime
import configparser
import random
from pytz import timezone
from mastodon import Mastodon

from . import KotohiraMemory

config = configparser.ConfigParser()
config.read('config/config.ini')

mastodon = Mastodon(
    access_token='config/accesstoken.txt',
    api_base_url=config['instance']['address']
)

class Yu:
    @staticmethod
    def timeReport():
        now = datetime.datetime.now(timezone('Asia/Tokyo'))
        nowH = now.strftime("%H")
        if nowH == "12":
            mastodon.toot(f"琴平ユウちゃんが正午をお知らせしますっ！")
        elif nowH == "23":
            mastodon.toot(f"琴平ユウちゃんがテレホタイムをお知らせしますっ！")
        elif nowH == "00" or nowH == "0":
            mastodon.toot(f"琴平ユウちゃんが日付が変わったことをお知らせしますっ！")
        else:
            mastodon.toot(f"琴平ユウちゃんが{nowH}時をお知らせしますっ！")

    @staticmethod
    def fortune(mentionId, acctId):
        # 乱数作成
        rnd = random.randrange(5)
        print(f"占いっ！：@{acctId} => {rnd}")
        if rnd == 0:
            mastodon.status_post(f'@{acctId}\n🎉 大吉ですっ！', in_reply_to_id=mentionId)
        if rnd == 1:
            mastodon.status_post(f'@{acctId}\n👏 吉ですっ！', in_reply_to_id=mentionId)
        if rnd == 2:
            mastodon.status_post(f'@{acctId}\n👍 中吉ですっ！', in_reply_to_id=mentionId)
        if rnd == 3:
            mastodon.status_post(f'@{acctId}\n😞 末吉ですっ', in_reply_to_id=mentionId)
        if rnd == 4:
            mastodon.status_post(f'@{acctId}\n😥 凶ですっ・・・。', in_reply_to_id=mentionId)
    
    @staticmethod
    def meow_time():
        mastodon.toot("にゃんにゃん！")

    @staticmethod
    def msg_hook(tableName, coolDown, sendFormat, status, ktMemory):
        # タイムラインで正規表現にかかった場合に実行
        # status(生の情報)とKotohiraMemoryクラス情報を受け流す必要がある
        userInfo = ktMemory.select(tableName, status['account']['id'])
        now = datetime.datetime.now(timezone('Asia/Tokyo'))
        dt = now.strftime("%Y-%m-%d %H:%M:%S%z")
        if len(userInfo) == 0:
            # データがない場合はデータ挿入して実行
            ktMemory.insert(tableName, status['account']['id'], dt)
            doIt = True
        else:
            didWBAt = userInfo[0][2]
            didWBAtRaw = datetime.datetime.strptime(didWBAt, '%Y-%m-%d %H:%M:%S%z')
            dateDiff = now - didWBAtRaw
            # 前回の実行から指定秒数までクールダウンしたかを確認して実行するか決める
            if dateDiff.seconds >= coolDown:
                doIt = True
            else:
                doIt = False

        if doIt:
            mastodon.toot(status)
            ktMemory.update(tableName, dt, status['account']['id'])
        
        return doIt