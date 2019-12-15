import configparser
import datetime
import random
import re
import time
from sqlite3 import OperationalError

import requests.exceptions
from mastodon import Mastodon, StreamListener
from mastodon.Mastodon import MastodonNetworkError, MastodonServerError
from pytz import timezone
from Yu import KotohiraMemory, Util as KotohiraUtil, YuChan
from Yu.listener import user_listener, local_listener
from Yu.config import config

mastodon = Mastodon(
    access_token='config/accesstoken.txt',
    api_base_url=config['instance']['address']
)

def local():
    print('Initializing feature: local')
    try:
        mastodon.stream_local(local_listener(), timeout=20)
    except OperationalError as exc:
        print('＊データベースにアクセスできませんっ！ユウちゃん寝ますっ！')
        raise exc
    except (requests.exceptions.ReadTimeout, MastodonNetworkError, MastodonServerError):
        print('＊ローカルタイムラインが繋がんないみたいですっ・・・。１分後にやり直しますっ！')
        time.sleep(60)
        local()
    except:
        KotohiraUtil.PANIC()
        print('ローカルタイムラインを十秒待って読み込みし直しますねっ！')
        time.sleep(10)
        local()

def home():
    print('Initializing feature: home')
    print('Connect address: {}'.format(config['instance']['address']))
    try:
        res = mastodon.account_verify_credentials()
        print('Fetched account: @{}'.format(res.acct))
        mastodon.stream_user(user_listener(), timeout=20)
    except OperationalError as exc:
        print('＊データベースにアクセスできませんっ！ユウちゃん寝ますっ！')
        raise OperationalError from exc
    except (requests.exceptions.ReadTimeout, MastodonNetworkError, MastodonServerError):
        print('＊ホームタイムラインが繋がんないみたいですっ・・・。１分後にやり直しますっ！')
        time.sleep(60)
        home()
    except:
        KotohiraUtil.PANIC()
        print('ホームタイムラインを十秒待って読み込みし直しますねっ！')
        time.sleep(10)
        home()
