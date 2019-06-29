# -*- coding: utf-8 -*-

import os
import configparser
import glob
import sqlite3
import traceback
import json
from bottle import route, run, auth_basic, abort, response, request
from sqlite3 import OperationalError
from jinja2 import Template, Environment, FileSystemLoader

config = configparser.ConfigParser()
config.read('config/config.ini')

ENV = Environment(loader=FileSystemLoader('consoleTemplate'))

def VERIFY(username, password):
    return username == config['web']['user'] and password == config['web']['pass']

@route('/')
@auth_basic(VERIFY)
def index():
    return ENV.get_template('index.html').render()

@route('/panic-log')
@route('/panic-log/')
@auth_basic(VERIFY)
def list_panicLog():
    panicLogList = glob.glob("panic-log/PANIC-*.TXT")
    link = []
    for l in panicLogList:
        link.append(l.replace('panic-log/PANIC-', '').replace('.TXT', ''))
    link.sort()
    return ENV.get_template('panicList.html').render({'panicLists': link})

@route('/db')
@route('/db/')
@auth_basic(VERIFY)
def list_table():
    try:
        conn = sqlite3.connect('Yu_{}.db'.format(config['instance']['address']))
        c = conn.cursor()
        c.execute("select name from sqlite_master where type='table'")
        tableLists = []
        for tbl in c.fetchall():
            tableLists.append(tbl[0])
        tableLists.sort()
    except:
        traceback.print_exc()
        abort(404, "TABLE NOT FOUND")
    else:
        return ENV.get_template('dbList.html').render({'tableLists': tableLists})
    finally:
        conn.close()

@route('/db/<table:re:[a-z_]+>')
@auth_basic(VERIFY)
def list_dbtable(table):
    try:
        LIMIT = 100
        conn = sqlite3.connect('Yu_{}.db'.format(config['instance']['address']))
        c = conn.cursor()
        tableColumns = []

        for tn in c.execute(f"PRAGMA table_info('{table}')"):
            tableColumns.append(tn[1])
        
        for tc in c.execute(f"SELECT count() FROM {table}"):
            TABLECOUNT = tc[0]

        operate = f"SELECT * FROM {table}"

        sort = request.query.get('sort')
        sort = "" if sort is None else sort
        order = request.query.get('order')
        order = "" if order is None else order
        page = request.query.get('page')
        page = 0 if page is None else int(page)

        if sort != "":
            operate += f" ORDER BY {sort}"
        
        if sort != "" and order != "":
            if order == "1":
                operate += f" ASC"
            else:
                operate += f" DESC"

        offset = page * LIMIT
        operate += f" LIMIT {LIMIT} OFFSET {offset}"
        previousPage = page - 1
        nextPage =  page + 1

        if int(page) <= 0:
            previousDisable = True
        else:
            previousDisable = False

        if offset + 100 >= TABLECOUNT:
            nextDisable = True
        else:
            nextDisable = False

        tableBodies = []
        for tb in c.execute(operate):
            tableBody = []
            for i in tb:
                tableBody.append(i)
            tableBodies.append(tableBody)

        return ENV.get_template('tableShow.html').render({'tableName': table,
                                                          'tableColumns': tableColumns,
                                                          'tableBodies': tableBodies,
                                                          'previousDisable': previousDisable,
                                                          'nextDisable': nextDisable,
                                                          'currentPage': page,
                                                          'previousPage': previousPage,
                                                          'nextPage': nextPage,
                                                          'sort': sort,
                                                          'order': order})
    except:
        traceback.print_exc()
        abort(404, "TABLE NOT FOUND")
    finally:
        conn.close()

@route('/panic-log/<panicdate:int>')
@auth_basic(VERIFY)
def show_panicLog(panicdate):
    if os.path.isdir('panic-log') and os.path.isfile(f'panic-log/PANIC-{str(panicdate)}.TXT'):
        with open(f'panic-log/PANIC-{str(panicdate)}.TXT', encoding="utf-8") as panic:
            txtRaw = panic.read()
        response.content_type = "text/plain"
        return txtRaw
    else:
        abort(404, "PANIC LOG NOT FOUND")

def WEBRUN():
    run(port=7878)
