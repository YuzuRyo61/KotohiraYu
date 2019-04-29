# -*- coding: utf-8 -*-

import configparser
import sqlite3
import glob
import os

config = configparser.ConfigParser()
config.read('config/config.ini')

class KotohiraMemory:
    def __init__(self, showLog=False):
        self.showLog = showLog
        # データベースが存在しない場合、コネクト後にテーブル作成処理を行う
        if not os.path.isfile('Yu_{}.db'.format(config['instance']['address'])):
            tableInit = True
        else:
            tableInit = False

        # データベースコネクト
        self.conn = sqlite3.connect('Yu_{}.db'.format(config['instance']['address']))
        self.cursor = self.conn.cursor()

        # データベーステーブル初期化
        if tableInit:
            self.init_table()
        
        self.__log('CONNECT')

    def init_table(self, table=None):
        # "!INIT"フォルダにあるSQLファイルのリストを読み込み、1つずつSQLを実行していく
        self.__log('TABLE INIT')
        if table == None:
            # テーブルが未指定の場合は"!INIT"フォルダ内にあるsqlファイルをすべて読みこんでテーブル作成
            init_sqls = glob.glob('sql/!INIT/*.sql')
            for sql in init_sqls:
                with open(sql, "r") as s:
                    schema = s.read()
                    self.cursor.execute(schema)
                    self.__log(f'Insert: {sql}')
        else:
            # テーブル指定があった場合はそのファイルを開き挿入
            if os.path.isfile(f'sql/!INIT/{table}.sql'):
                with open(f'sql/!INIT/{table}.sql', 'r') as s:
                    schema = s.read()
                    self.cursor.execute(schema)
                    self.__log(f'Insert: {table}')
            else:
                raise Exception(f"Init SQL file was not found: {table}")

    def close(self, DISCARD=False):
        # 接続終了処理。DISCARDがTrueになってる場合はコミットせずに切断する
        if not DISCARD:
            self.__log('COMMIT')
            self.conn.commit()
        self.conn.close()

    def commit(self):
        # 単にコミットだけ行う
        self.conn.commit()
        self.__log('COMMIT')

    def __del__(self):
        # del命令がかかったらclose関数を呼ぶ。コミットも自動的に行う
        self.close()

    def __log(self, message):
        # ログ表示用。ただしクラス初期化時にログ表示をするように設定する必要がある or (クラス変数).showLog をTrueに変更すればログ表示可
        if self.showLog:
            print(f"[DATABASE] {message}")

    def insert(self, table, *args):
        # SQLファイルに沿ってデータ挿入（指定したテーブルのフォルダ内のinsert.sqlファイル）
        if os.path.isfile(f"sql/{table}/insert.sql"):
            with open(f"sql/{table}/insert.sql") as sqltxt:
                sql = sqltxt.read()
                self.cursor.execute(sql, args)
                self.__log(f"Insert: {table} => {args}")
        else:
            raise Exception(f"Insert SQL file was not found: {table}")

    def select(self, table, *args):
        # SQLファイルに沿ってデータ検索（指定したテーブルのフォルダ内のselect.sqlファイル）
        if os.path.isfile(f"sql/{table}/select.sql"):
            with open(f"sql/{table}/select.sql") as sqltxt:
                sql = sqltxt.read()
                self.cursor.execute(sql, args)
                self.__log(f"Select: {table} => {args}")
                return self.cursor.fetchall()
        else:
            raise Exception(f"Select SQL file was not found: {table}")

    def update(self, table, *args):
        # SQLファイルに沿ってデータ変更（指定したテーブルのフォルダ内のupdate.sqlファイル）
        if os.path.isfile(f"sql/{table}/update.sql"):
            with open(f"sql/{table}/update.sql") as sqltxt:
                sql = sqltxt.read()
                self.cursor.execute(sql, args)
                self.__log(f"Update: {table} => {args}")
        else:
            raise Exception(f"Update SQL file was not found: {table}")

    def delete(self, table, *args):
        # SQLファイルに沿ってデータ削除（指定したテーブルのフォルダ内のdelete.sqlファイル）
        if os.path.isfile(f"sql/{table}/delete.sql"):
            with open(f"sql/{table}/delete.sql") as sqltxt:
                sql = sqltxt.read()
                self.cursor.execute(sql, args)
                self.__log(f"Delete: {table} => {args}")
        else:
            raise Exception(f"Delete SQL file was not found: {table}")
