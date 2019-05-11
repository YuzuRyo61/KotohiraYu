# -*- coding: utf-8 -*-

import os
import configparser
import glob
import sqlite3
import traceback
import json
from bottle import route, run, auth_basic, abort, response
from sqlite3 import OperationalError

config = configparser.ConfigParser()
config.read('config/config.ini')

def VERIFY(username, password):
    return username == config['web']['user'] and password == config['web']['pass']

@route('/')
@auth_basic(VERIFY)
def index():
    return """<!DOCTYPE html>
    <html>
      <head>
        <title>Yu-Console</title>
      </head>
      <body>
        <ul>
          <li><a href="panic-log">PANIC LOG</a></li>
        </ul>
      </body>
    </html>
    """

@route('/panic-log')
@route('/panic-log/')
@auth_basic(VERIFY)
def list_panicLog():
    panicLogList = glob.glob("panic-log/PANIC-*.TXT")
    output = "<!DOCTYPE html><html><head><title>PANICLOG</title></head><body><h1>PANICLOG</h1><ul>"
    link = ""
    for l in panicLogList:
        link = l.replace('panic-log/PANIC-', '').replace('.TXT', '')
        output += f'<li><a href="/panic-log/{link}">{link}</a></li>'
    output += '</ul></body></html>\n'
    return output

@route('/db')
@route('/db/')
@auth_basic(VERIFY)
def list_table():
    return "Underconstruction"

@route('/db/<table:re:[a-z_]+>')
@auth_basic(VERIFY)
def list_dbtable(table):
    try:
        conn = sqlite3.connect('Yu_{}.db'.format(config['instance']['address']))
        c = conn.cursor()
        output = f"<!DOCTYPE html><html><head><title>TABLE SHOW: {table}</title></head><body><h1>TABLE SHOW: {table}</h1><table>"
        output += "<tr>"
        for tn in c.execute(f"PRAGMA table_info('{table}')"):
            output += f"<th>{tn[1]}</th>"
        output += "</tr>"
        for tb in c.execute(f"SELECT * FROM {table}"):
            output += f"<tr>"
            for i in tb:
                output += f"<td>{i}</td>"
            output += f"</tr>"
        output += "</table></body>"
        return output
    except:
        traceback.print_exc()
        abort(404, "TABLE NOT FOUND")
    finally:
        conn.close()

@route('/user-memos/<date:re:[0-9_+]+>')
@auth_basic(VERIFY)
def list_usermemos(date):
    try:
        conn = sqlite3.connect('Yu_{}.db'.format(config['instance']['address']))
        c = conn.cursor()
        c.execute('SELECT * FROM user_memos WHERE memo_time = ?', (date, ))
        memoRaw = c.fetchone()
        if memoRaw == None:
            abort(404, "This memo time was not found")
        else:
            memo = json.loads(memoRaw[2], encoding="utf-8")
            output = f"<!DOCTYPE html><html><head><title>UESR MEMO SHOW: {date}</title></head><body><h1>UESR MEMO SHOW: {date}</h1><table><tr><th>User</th><th>Memo</th></tr>"
            for me in memo:
                output += f"<tr><td><a href=\"https://{config['instance']['address']}/@{me['from']}\">@{me['from']}</a></td><td>{me['body']}</td></tr>"
            output += "</table></body>\n"
            return output
    except OperationalError:
        traceback.print_exc()
        abort(500, "INTERNAL SERVER ERROR")
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
