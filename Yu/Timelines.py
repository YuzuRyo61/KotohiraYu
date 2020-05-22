import sys
import datetime
import random
import re
import time
import json
from sqlite3 import OperationalError

import requests
import requests.exceptions
import sseclient
from mastodon import StreamListener
from mastodon.Mastodon import MastodonNetworkError, MastodonServerError
from pytz import timezone
from Yu import Util as KotohiraUtil, YuChan, log
from Yu.listener.local import local_onDelete, local_onUpdate
from Yu.listener.home import home_onUpdate, home_onNotification
from Yu.config import config
from Yu.mastodon import mastodon

def local():
    log.logInfo('Initializing feature: local')
    # SSE status test
    try:
        requests.get(f'https://{config["instance"]["address"]}/api/v1/streaming/health').raise_for_status()
    except requests.exceptions.HTTPError as exc:
        log.logCritical('＊Server-sent eventsが使えませんっ！ユウちゃん寝ますっ！')
        raise exc
    
    try:
        while True:
            client = sseclient.SSEClient(
                requests.get(
                    f'https://{config["instance"]["address"]}/api/v1/streaming/public/local?access_token={config["instance"]["access_token"]}',
                    stream=True
                )
            )
            for event in client.events():
                if event.event == "update":
                    local_onUpdate(json.loads(event.data))
                elif event.event == "delete":
                    local_onDelete(event.data)
                else:
                    log.logWarn(f"Unknown event: {event.event}")
            log.logErr('サーバーからの通信が切れましたっ！１分後にやり直しますっ！')
            time.sleep(60)
    except OperationalError as exc:
        log.logCritical('＊データベースにアクセスできませんっ！ユウちゃん寝ますっ！')
        raise exc
    except (requests.exceptions.ReadTimeout, MastodonNetworkError, MastodonServerError):
        log.logErr('＊ローカルタイムラインが繋がんないみたいですっ・・・。１分後にやり直しますっ！')
        time.sleep(60)
        local()
    except KeyboardInterrupt:
        pass
    except:
        KotohiraUtil.PANIC(sys.exc_info())
        log.logErr('ローカルタイムラインを30秒待って読み込みし直しますねっ！')
        time.sleep(30)
        local()

def home():
    log.logInfo('Initializing feature: home')
    log.logInfo('Connect address: {}'.format(config['instance']['address']))
    # SSE status test
    try:
        requests.get(f'https://{config["instance"]["address"]}/api/v1/streaming/health').raise_for_status()
    except requests.exceptions.HTTPError as exc:
        log.logCritical('＊Server-sent eventsが使えませんっ！ユウちゃん寝ますっ！')
        raise exc

    try:
        res = mastodon.account_verify_credentials()
        log.logInfo('Fetched account: @{}'.format(res.acct))
        while True:
            client = sseclient.SSEClient(
                requests.get(
                    f'https://{config["instance"]["address"]}/api/v1/streaming/user?access_token={config["instance"]["access_token"]}',
                    stream=True
                )
            )
            for event in client.events():
                if event.event == "update":
                    home_onUpdate(json.loads(event.data))
                elif event.event == "notification":
                    home_onNotification(json.loads(event.data))
                elif event.event == "delete":
                    pass
                else:
                    log.logWarn(f"Unknown event: {event.event}")
            log.logErr('サーバーからの通信が切れましたっ！１分後にやり直しますっ！')
            time.sleep(60)
    except OperationalError as exc:
        log.logCritical('＊データベースにアクセスできませんっ！ユウちゃん寝ますっ！')
        raise exc
    except (requests.exceptions.ReadTimeout, MastodonNetworkError, MastodonServerError):
        log.logErr('＊ホームタイムラインが繋がんないみたいですっ・・・。１分後にやり直しますっ！')
        time.sleep(60)
        home()
    except KeyboardInterrupt:
        pass
    except:
        KotohiraUtil.PANIC(sys.exc_info())
        log.logErr('ホームタイムラインを十秒待って読み込みし直しますねっ！')
        time.sleep(10)
        home()
