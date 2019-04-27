from mastodon import Mastodon, StreamListener
import datetime
from pytz import timezone
import configparser
import time
import re
import requests.exceptions

# デバッグ用！
import pprint as pp

from Yu import KotohiraUtil, KotohiraMemory, Yu

config = configparser.ConfigParser()
config.read('config/config.ini')

mastodon = Mastodon(
    access_token='config/accesstoken.txt',
    api_base_url=config['instance']['address']
)

# ホームタイムラインのリスナー(主に通知リスナー)
class user_listener(StreamListener):
    def on_notification(self, notification):
        # 代入してちょっと見栄え良く
        notifyType = notification['type']
        if notifyType == 'mention':
            # 返信とか

            # テキスト化
            txt = KotohiraUtil.h2t(notification['status']['content'])

            # bot属性のアカウントの場合は無視する
            if notification['account']['bot'] == True:
                return

            # とりあえずふぁぼる
            print('お手紙っ！：@{0} < {1}'.format(notification['account']['acct'], txt))
            mastodon.status_favourite(notification['status']['id'])

            # 好感度を少し上げる
            memory = KotohiraMemory(showLog=config['log'].getboolean('enable'))
            memory.update('fav_rate', 1, notification['account']['id'])

            # 正規表現とか
            followReq = re.search(r'(フォロー|[Ff]ollow|ふぉろー)(して|.?頼(む|みたい|もう)|.?たの(む|みたい|もう)|お願い|おねがい)', txt)
            fortune = re.search(r'(占|うらな)(って|い)', txt)

            # メンションでフォローリクエストされたとき
            # (作成途中っ)
            if followReq:
                pass
            
            # 占いのリクエストがされたとき
            if fortune:
                Yu.fortune(notification['status']['id'], notification['account']['acct'])
                # 更に４つ加算
                memory.update('fav_rate', 4, notification['account']['id'])
            
            # クローズと共に保存
            del memory
        
        elif notifyType == 'favourite':
            # ふぁぼられ
            print('ふぁぼられたっ！：@{0}'.format(notification['account']['acct']))
            # ふぁぼ連対策
            memory = KotohiraMemory(showLog=config['log'].getboolean('enable'))
            favInfo = memory.select('recent_favo', notification['account']['id'])
            if len(favInfo) == 0:
                # データがない場合は追加して好感度アップ
                memory.insert('recent_favo', notification['account']['id'], notification['status']['id'])
                memory.update('fav_rate', 1, notification['account']['id'])
            else:
                # 最後にふぁぼったトゥートが同じものでないこと
                if notification['status']['id'] != favInfo[0][2]:
                    memory.update('recent_favo', notification['status']['id'], notification['account']['id'])
                    memory.update('fav_rate', 1, notification['account']['id'])
            
            # コミット
            del memory

        
        elif notifyType == 'reblog':
            # ブーストされ
            print('ブーストされたっ！：@{0}'.format(notification['account']['acct']))
            # ふぁぼられと同様な機能とか
        
        elif notifyType == 'follow':
            # フォローされ
            print('フォローされたっ！：@{0}'.format(notification['account']['acct']))

# ローカルタイムラインのリスナー
class local_listener(StreamListener):
    def on_update(self, status):
        # Botアカウントは応答しないようにする
        if status['account']['bot'] == True:
            return

        # 自分のトゥートは無視
        if config['user']['me'] == status['account']['acct']:
            return

        # トゥート内のHTMLタグを除去
        txt = KotohiraUtil.h2t(status['content'])

        # 自分宛てのメンションはここのリスナーでは無視する
        isMeMention = re.search('@{}'.format(config['user']['me']), txt)
        if isMeMention:
            return
        
        # データベース初期化
        memory = KotohiraMemory(showLog=config['log'].getboolean('enable'))

        # ユウちゃんが知ってるユーザーか調べる
        # 知らない場合はユウちゃんは記憶しますっ！
        isknown = memory.select('known_users', status['account']['id'])
        if len(isknown) == 0:
            now = datetime.datetime.now(timezone('Asia/Tokyo'))
            dt = now.strftime("%Y-%m-%d %H:%M:%S%z")
            memory.insert('known_users', status['account']['id'], status['account']['acct'], dt)
            memory.insert('fav_rate', status['account']['id'])
            memory.insert('updated_users', status['account']['id'], dt)
            print('覚えたっ！： @{0}'.format(status['account']['acct']))
            newUser = True
            # トゥートカウントが10以下の場合は新規さん向けの挨拶しますっ！
            if status['account']['statuses_count'] <= 10:
                print('新規さん！: @{0}'.format(status['account']['acct']))
                mastodon.status_reblog(status['id'])
                mastodon.toot('新規さんっ！はじめましてっ！琴平ユウって言いますっ！\nよろしくねっ！\n\n@{0}'.format(status['account']['acct']))
        else:
            newUser = False

        # 正規表現チェック
        calledYuChan = re.search(r'(琴平|ことひら|コトヒラ|ｺﾄﾋﾗ|ゆう|ユウ|ﾕｳ)', txt)
        iBack = re.search(r'(帰宅|ただいま|帰った|帰還)(?!.*(する|します|しちゃう|しよう))', txt)
        passage = re.search(r'(通過|つうか|ツウカ)', txt)
        sinkiSagi = re.search(r'(新規|しんき)(です|だよ|なのじゃ)', txt)
        
        # ユウちゃん etc... とか呼ばれたらふぁぼる
        if calledYuChan:
            print('呼ばれたっ！：@{0} < {1}'.format(status['account']['acct'], txt))
            mastodon.status_favourite(status['id'])
            # 好感度ちょいアップ
            memory.update('fav_rate', 1, status['account']['id'])

        # 帰ったよ〜 とか言ったらトゥート
        if iBack:
            # データベースからデータ取得
            userInfo = memory.select('wel_back', status['account']['id'])
            now = datetime.datetime.now(timezone('Asia/Tokyo'))
            dt = now.strftime("%Y-%m-%d %H:%M:%S%z")
            if len(userInfo) == 0:
                # データがない場合はデータ挿入しておかえり実行
                memory.insert('wel_back', status['account']['id'], dt)
                doIt = True
            else:
                didWBAt = userInfo[0][2]
                didWBAtRaw = datetime.datetime.strptime(didWBAt, '%Y-%m-%d %H:%M:%S%z')
                dateDiff = now - didWBAtRaw
                # 前回の「帰ったよ」etc...から10分以上経過していれば応答する
                if dateDiff.seconds >= 600:
                    doIt = True
                else:
                    doIt = False

            if doIt:
                print('おかえりっ！：@{0} < {1}'.format(status['account']['acct'], txt))
                mastodon.toot("""{0}さん、おかえりなさいませっ！""".format(repr(status['account']['display_name'])[1:-1]))
                memory.update('wel_back', dt, status['account']['id'])

        # 通過 とか言ったら阻止しちゃうよっ！
        if passage:
            userInfo = memory.select('passage', status['account']['id'])
            now = datetime.datetime.now(timezone('Asia/Tokyo'))
            dt = now.strftime("%Y-%m-%d %H:%M:%S%z")
            if len(userInfo) == 0:
                # データがない場合はデータ挿入して阻止実行
                memory.insert('passage', status['account']['id'], dt)
                doIt = True
            else:
                didAt = userInfo[0][2]
                didAtRaw = datetime.datetime.strptime(didAt, '%Y-%m-%d %H:%M:%S%z')
                dateDiff = now - didAtRaw
                # 前回の「通過」etc...から5分以上経過していれば応答する
                if dateDiff.seconds >= 300:
                    doIt = True
                else:
                    doIt = False
            
            if doIt:
                print('阻止っ！：@{0} < {1}'.format(status['account']['acct'], txt))
                mastodon.toot('阻止っ！！(*`ω´*)')
                memory.update('passage', dt, status['account']['id'])
        
        if sinkiSagi and status['account']['statuses_count'] > 10:
            # 新規詐欺見破りっ！
            userInfo = memory.select('sin_sagi', status['account']['id'])
            now = datetime.datetime.now(timezone('Asia/Tokyo'))
            dt = now.strftime("%Y-%m-%d %H:%M:%S%z")
            if len(userInfo) == 0:
                # データがない場合はデータ挿入して新規詐欺見破り実行
                memory.insert('sin_sagi', status['account']['id'], dt)
                doIt = True
            else:
                didAt = userInfo[0][2]
                didAtRaw = datetime.datetime.strptime(didAt, '%Y-%m-%d %H:%M:%S%z')
                dateDiff = now - didAtRaw
                # 前回の詐欺の「新規だよ」etc...から5分以上経過していれば応答する
                if dateDiff.seconds >= 300:
                    doIt = True
                else:
                    doIt = False
            
            if doIt:
                print('新規詐欺っ！:@{0} < {1}'.format(status['account']['acct'], txt))
                mastodon.toot('新規詐欺は行けませんっ！！(*`ω´*)')
                memory.update('sin_sagi', status['account']['id'], dt)
        # 最終更新を変更
        now = datetime.datetime.now(timezone('Asia/Tokyo'))
        dt = now.strftime("%Y-%m-%d %H:%M:%S%z")
        # ２重更新防策
        if not newUser:
            updated_at = memory.select('updated_users', status['account']['id'])[0]
            updatedAtRaw = datetime.datetime.strptime(updated_at[2], '%Y-%m-%d %H:%M:%S%z')
            dateDiff = now - updatedAtRaw
            # 3時間以上更新がなかった場合は挨拶する
            if dateDiff.seconds >= 10800:
                print("こんにちはっ！：@{0} < {1}".format(status['account']['acct'], txt))
                mastodon.toot("""{0}さん、こんにちはっ！""".format(repr(status['account']['display_name'])[1:-1]))
            memory.update('updated_users', dt, status['account']['id'])

        # データベース切断
        del memory

def local():
    print('Initializing feature: local')
    try:
        mastodon.stream_local(local_listener(), timeout=20)
    except requests.exceptions.ReadTimeout:
        print('＊ローカルタイムラインが繋がんないみたいですっ・・・。１分後にやり直しますっ！')
        time.sleep(60)
        local()
    except:
        KotohiraUtil.PANIC()
        print('ローカルタイムラインを五秒待って読み込みし直しますねっ！')
        time.sleep(5)
        local()

def home():
    print('Initializing feature: home')
    print('Connect address: {}'.format(config['instance']['address']))
    try:
        res = mastodon.account_verify_credentials()
        print('Fetched account: @{}'.format(res.acct))
        mastodon.stream_user(user_listener(), timeout=20)
    except requests.exceptions.ReadTimeout:
        print('＊ホームタイムラインが繋がんないみたいですっ・・・。１分後にやり直しますっ！')
        time.sleep(60)
        home()
    except:
        KotohiraUtil.PANIC()
        print('ホームタイムラインを五秒待って読み込みし直しますねっ！')
        time.sleep(5)
        home()
