#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Kotohira Yu

YuzuRyo61 Presents

License: MIT License (See LICENSE)
"""

import threading
import sys
import os

from Yu import Yu, KotohiraUtil, local, home

def main():
    features = []
    features.append( threading.Thread(target=local) )
    features.append( threading.Thread(target=home) )

    try:
        for ft in features:
            ft.start()
    except KeyboardInterrupt:
        sys.exit()
    except:
        KotohiraUtil.PANIC()

if __name__ == '__main__':
    if not os.path.isfile('config/config.ini') or not os.path.isfile('config/accesstoken.txt'):
        print('＊設定ファイルやアクセストークンがありませんっ！！')
        sys.exit(1)
    main()
