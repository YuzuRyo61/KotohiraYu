# -*- coding: utf-8 -*-

import datetime
import configparser
import random
from pytz import timezone
from mastodon import Mastodon

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