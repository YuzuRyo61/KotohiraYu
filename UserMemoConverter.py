#!/usr/bin/env python3

"""
ユーザーメモのエスケープを修正するパッチスクリプト
※実行しなくても大きい問題はないです。
"""

import configparser
import os
import sqlite3
import json

if __name__ == "__main__":
    from Yu.config import config
    print('Selected DB: Yu_{}.db'.format(config['instance']['address']))
    if os.path.isfile('Yu_{}.db'.format(config['instance']['address'])):
        CONNECT = sqlite3.connect('Yu_{}.db'.format(config['instance']['address']))
        CURSOR = CONNECT.cursor()
        memoDB = CURSOR.execute('SELECT * FROM `user_memos`')
        for memo in memoDB.fetchall():
            print(f'CONVERT: {memo[1]}')
            print(memo[2])
            memoJson = json.loads(memo[2], encoding='utf-8')
            memoDump = json.dumps(memoJson, ensure_ascii=False)
            print(memoDump)
            if memo[2] == memoDump:
                print(f'CONVERT SKIP: {memo[1]}')
            try:
                CURSOR.execute('UPDATE `user_memos` SET body = ? WHERE memo_time = ?', (memoDump, memo[1]))
            except Exception:
                print('CONVERT FAILED: {}'.format(memo[1]))

        CONNECT.commit()
        CONNECT.close()
        print('CONVERT COMPLETE')
    else:
        print('データベースファイルがないため、このパッチを適用する必要がありません。')
