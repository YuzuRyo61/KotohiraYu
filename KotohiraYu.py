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
from sqlite3 import OperationalError

from mastodon import Mastodon

from Yu import YuChan, KotohiraMemory, local, home, WEBRUN
from Yu import Util as KotohiraUtil
from Yu.config import config

mastodon = Mastodon(
    access_token='config/accesstoken.txt',
    api_base_url=config['instance']['address']
)

def main():
    # スレッド化するための初期化
    features = []
    # タイムライン系
    features.append( threading.Thread(target=local) )
    features.append( threading.Thread(target=home) )
    # cron系
    features.append( threading.Thread(target=KotohiraUtil.schedule, args=(YuChan.timeReport,['**:00'])) )
    features.append( threading.Thread(target=KotohiraUtil.schedule, args=(YuChan.toot_memo, ['**:55'])) )
    features.append( threading.Thread(target=KotohiraUtil.schedule, args=(YuChan.meow_time, ['22:22'])) )
    # ウェブコンソール（不要な場合はconfigファイルで）
    # ポート番号は 7878 でListenされます
    if config['web']['enable']:
        features.append( threading.Thread(target=WEBRUN) )

    try:
        # スレッド開始
        for ft in features:
            ft.start()
        print("ALL SYSTEMS READY!")
    except KeyboardInterrupt:
        # 動作する気はしない
        sys.exit()
    except OperationalError:
        print("DATABASE ACCESS ERROR")
        sys.exit(2)
    except:
        KotohiraUtil.PANIC()

if __name__ == '__main__':
    # 設定ファイルがあるかチェック。ない場合は弾く
    if os.path.isfile('config/config.toml') and os.path.isfile('config/accesstoken.txt'):
        # config.tomlにあるIDと実際に取り寄せたIDが一致しない場合は弾く
        res = mastodon.account_verify_credentials()
        if config['user']['me'] != res.acct:
            print('＊設定したアカウントIDと一致しませんっ！！')
            sys.exit(1)

        # 問題なさそうであれば起動

        # データベース初期化
        km = KotohiraMemory(showLog=config['log']['enable'])
        del km

        main()
    else:
        print('＊設定ファイルやアクセストークンがありませんっ！！')
        sys.exit(1)
