#!/usr/bin/env python3

"""
Version 4.0以降用 データベース移行ツール
"""
import os
import sys
import sqlite3
import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

if __name__ == "__main__":
    try:
        from Yu.database import DATABASE
        from Yu.config import config
        from Yu.models import known_users, fav_rate, nickname, user_memos, updated_users
        if not os.path.isfile(f"Yu_{config['instance']['address']}.db"):
            print("データベースファイルが見つかりません。Version 4.0以降から使用する場合はこのツールを使用する必要はありません。")
            sys.exit(1)
    except Exception as e:
        print(e)
        print("エラーが発生しました。このスクリプトを実行する前にconfig.tomlを設定してください。")
        sys.exit(1)

    print("""
    続行する前に・・・
    設定しているデータベースが空であることを確認し、`pipenv run migrate`を実行してください。
    また、データベースのバックアップを保存することを推奨します。
    データが移行されるテーブルは以下の通りです：
    ・known_users
    ・updated_users
    ・fav_rate
    ・nickname
    ・user_memos
    続行する場合はEnterキーを押します。
    """)
    input()

    CONNECT = sqlite3.connect('Yu_{}.db'.format(config['instance']['address']))
    CURSOR = CONNECT.cursor()

    with DATABASE.atomic():
        # known_users
        print("=== known_users ===")
        for userData in CURSOR.execute('SELECT * FROM `known_users`').fetchall():
            parsedDate = datetime.datetime.strptime(userData[3], "%Y-%m-%d %H:%M:%S%z")
            print(f"{userData[1]} | {userData[2]} | {parsedDate}")
            known_users.create(ID_Inst=userData[1], acct=userData[2], known_at=parsedDate)

        # updated_users
        print("=== updated_users ===")
        for userUpdate in CURSOR.execute('SELECT * FROM `updated_users`').fetchall():
            user = known_users.get_or_none(known_users.ID_Inst == userUpdate[1])
            print(f"{userUpdate[1]} | {userUpdate[2]}")
            updated_users.create(ID_Inst=user, date=userUpdate[2])
        
        # fav_rate
        print("=== fav_rate ===")
        for userRate in CURSOR.execute('SELECT * FROM `fav_rate`').fetchall():
            user = known_users.get_or_none(known_users.ID_Inst == userRate[1])
            print(f"{userRate[1]} | {userRate[2]}")
            fav_rate.create(ID_Inst=user, rate=userRate[2])
    
        # nickname
        print("=== nickname ===")
        for userNick in CURSOR.execute('SELECT * FROM `nickname`').fetchall():
            user = known_users.get_or_none(known_users.ID_Inst == userNick[1])
            print(f"{userNick[1]} | {userNick[2]}")
            nickname.create(ID_Inst=user, nickname=userNick[2])
        
        # user_memos
        print("=== user_memos ===")
        for userMemo in CURSOR.execute('SELECT * FROM `user_memos`').fetchall():
            print(f"{userMemo[1]} | {userMemo[2]}")
            user_memos.create(memo_time=userMemo[1], body=userMemo[2])

    if not DATABASE.is_closed():
        DATABASE.commit()
        DATABASE.close()

    print("データベースの移行が完了しました。旧データベースは削除しても構いません。\n多重実行を防止するため、ファイル名の変更を推奨します。")
    print("Enterキーを押して終了します。")
    input()
    sys.exit()
