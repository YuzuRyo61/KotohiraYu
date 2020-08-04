import datetime
import json
import os
import random
import re
import signal
import sys
import time
from sqlite3 import OperationalError

import requests
import requests.exceptions
import sseclient
from pytz import timezone

from mastodon import StreamListener
from mastodon.Mastodon import (MastodonBadGatewayError, MastodonNetworkError,
                               MastodonServerError)
from Yu import Util as KotohiraUtil
from Yu import YuChan, log
from Yu.config import config
from Yu.listener.home import home_onNotification, home_onUpdate
from Yu.listener.local import local_onDelete, local_onUpdate
from Yu.mastodon import mastodon


def local(main_pid):
    log.logInfo('Initializing feature: local')
    # SSE status test
    try:
        requests.get(f'https://{config["instance"]["address"]}/api/v1/streaming/health').raise_for_status()
    except requests.exceptions.HTTPError as exc:
        log.logCritical('＊Server-sent eventsが使えませんっ！ユウちゃん寝ますっ！')
        os.kill(main_pid, signal.SIGKILL)
        return

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
        os.kill(main_pid, signal.SIGKILL)
        return
    except (requests.exceptions.ReadTimeout, requests.exceptions.ChunkedEncodingError, MastodonNetworkError, MastodonServerError, MastodonBadGatewayError):
        log.logErr('＊ローカルタイムラインが繋がんないみたいですっ・・・。１分後にやり直しますっ！')
        time.sleep(60)
        local(main_pid)
    except KeyboardInterrupt:
        pass
    except:
        KotohiraUtil.PANIC(sys.exc_info())
        log.logErr('ローカルタイムラインを30秒待って読み込みし直しますねっ！')
        time.sleep(30)
        local(main_pid)

def home(main_pid):
    log.logInfo('Initializing feature: home')
    log.logInfo('Connect address: {}'.format(config['instance']['address']))
    # SSE status test
    try:
        requests.get(f'https://{config["instance"]["address"]}/api/v1/streaming/health').raise_for_status()
    except requests.exceptions.HTTPError as exc:
        log.logCritical('＊Server-sent eventsが使えませんっ！ユウちゃん寝ますっ！')
        os.kill(main_pid, signal.SIGKILL)
        return

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
        os.kill(main_pid, signal.SIGKILL)
        return
    except (requests.exceptions.ReadTimeout, requests.exceptions.ChunkedEncodingError, MastodonNetworkError, MastodonServerError, MastodonBadGatewayError):
        log.logErr('＊ホームタイムラインが繋がんないみたいですっ・・・。１分後にやり直しますっ！')
        time.sleep(60)
        home(main_pid)
    except KeyboardInterrupt:
        pass
    except:
        KotohiraUtil.PANIC(sys.exc_info())
        log.logErr('ホームタイムラインを十秒待って読み込みし直しますねっ！')
        time.sleep(10)
        home(main_pid)
