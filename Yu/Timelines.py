import configparser
import datetime
import random
import re
import time
from sqlite3 import OperationalError

import requests.exceptions
from mastodon import StreamListener
from mastodon.Mastodon import MastodonNetworkError, MastodonServerError
from pytz import timezone
from Yu import Util as KotohiraUtil, YuChan, log
from Yu.listener import user_listener, local_listener
from Yu.config import config
from Yu.mastodon import mastodon

def local():
    log.logInfo('Initializing feature: local')
    try:
        mastodon.stream_local(local_listener(), timeout=20)
    except OperationalError as exc:
        log.logCritical('＊データベースにアクセスできませんっ！ユウちゃん寝ますっ！')
        raise exc
    except (requests.exceptions.ReadTimeout, MastodonNetworkError, MastodonServerError):
        log.logErr('＊ローカルタイムラインが繋がんないみたいですっ・・・。１分後にやり直しますっ！')
        time.sleep(60)
        local()
    except:
        KotohiraUtil.PANIC()
        log.logErr('ローカルタイムラインを十秒待って読み込みし直しますねっ！')
        time.sleep(10)
        local()

def home():
    log.logInfo('Initializing feature: home')
    log.logInfo('Connect address: {}'.format(config['instance']['address']))
    try:
        res = mastodon.account_verify_credentials()
        log.logInfo('Fetched account: @{}'.format(res.acct))
        mastodon.stream_user(user_listener(), timeout=20)
    except OperationalError as exc:
        log.logCritical('＊データベースにアクセスできませんっ！ユウちゃん寝ますっ！')
        raise OperationalError from exc
    except (requests.exceptions.ReadTimeout, MastodonNetworkError, MastodonServerError):
        log.logErr('＊ホームタイムラインが繋がんないみたいですっ・・・。１分後にやり直しますっ！')
        time.sleep(60)
        home()
    except:
        KotohiraUtil.PANIC()
        log.logErr('ホームタイムラインを十秒待って読み込みし直しますねっ！')
        time.sleep(10)
        home()
