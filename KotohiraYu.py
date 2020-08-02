#!/usr/bin/env python3
"""
Kotohira Yu

YuzuRyo61 Presents

License: MIT License (See LICENSE)
"""

# 意外にもみんなからソースコード分かりやすいって高評価受けてて驚きです。
# by 神様。

import threading
import sys
import os
import configparser

from Yu import YuChan, local, home, log
from Yu import Util as KotohiraUtil
from Yu.scheduler import run_scheduler
from Yu.config import config
from Yu.mastodon import mastodon
from Yu.database import DATABASE

def main():
    # スレッド化するための初期化
    features = []
    # タイムライン系
    features.append( threading.Thread(target=local, name='Timeline-Local', args=(os.getpid(), )) )
    features.append( threading.Thread(target=home, name='Timeline-Home', args=(os.getpid(), )) )
    # cron系
    features.append( threading.Thread(target=run_scheduler, name='Schedule'))

    try:
        # スレッド開始
        for ft in features:
            ft.setDaemon(True)
            ft.start()
        log.logInfo("ALL SYSTEMS READY!")
        for ft in features:
            ft.join()
    except KeyboardInterrupt:
        if not DATABASE.is_closed():
            DATABASE.close()
        sys.exit()
    except:
        KotohiraUtil.PANIC(sys.exc_info())

if __name__ == '__main__':
    # 設定ファイルがあるかチェック。ない場合は弾く
    if os.path.isfile('config/config.toml'):
        # config.tomlにあるIDと実際に取り寄せたIDが一致しない場合は弾く
        res = mastodon.account_verify_credentials()
        if config['user']['me'] != res.acct:
            log.logCritical('＊設定したアカウントIDと一致しませんっ！！')
            sys.exit(1)

        # 問題なさそうであれば起動
        main()
    else:
        log.logCritical('＊設定ファイルやアクセストークンがありませんっ！！')
        sys.exit(1)
