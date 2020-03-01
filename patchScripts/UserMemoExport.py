#!/usr/bin/env python3
"""
いままでのユーザーメモをエクスポートするスクリプト
"""

import configparser
import os
import sys
import sqlite3
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

if __name__ == "__main__":
    from Yu.config import config
    print('Selected DB: Yu_{}.db'.format(config['instance']['address']))
    if os.path.isfile('Yu_{}.db'.format(config['instance']['address'])):
        CONNECT = sqlite3.connect('Yu_{}.db'.format(config['instance']['address']))
        CURSOR = CONNECT.cursor()
        memoDB = CURSOR.execute('SELECT * FROM `user_memos`')
        memExportable = dict()
        for memo in memoDB.fetchall():
            print(f'EXPORT: {memo[1]}')
            memoJson = json.loads(memo[2], encoding='utf-8')
            memExportable[memo[1]] = memoJson

        CONNECT.commit()
        CONNECT.close()

        with open('USERMEMOS.json', 'w') as um:
            json.dump(memExportable, um, ensure_ascii=False, indent=4, separators=(',', ': '))

        print('EXPORT COMPLETE')
    else:
        print('データベースが存在しません。')
        sys.exit(1)
