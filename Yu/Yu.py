# -*- coding: utf-8 -*-

import datetime
import configparser
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