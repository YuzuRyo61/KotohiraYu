#!/usr/bin/env python3
"""
Database Migration tool
"""

# 直で実行している場合のみ作動
if __name__ == "__main__":
    import configparser
    import os
    from Yu import KotohiraMemory
    from Yu.config import config

    memory = KotohiraMemory(showLog=True)

    # データベースが存在している場合は実行する。
    # 存在しない場合は自動的にテーブル作成を行うので省略する
    if os.path.isfile('Yu_{}.db'.format(config['instance']['address'])):
        memory.init_table()

    # コミット
    del memory
    print('Migration Complete!')
