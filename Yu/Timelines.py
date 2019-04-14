from mastodon import Mastodon, StreamListener
import datetime
from pytz import timezone
import configparser
import time
import re

# デバッグ用！
import pprint as pp

from Yu import KotohiraUtil, KotohiraMemory

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
            txt = KotohiraUtil.h2t(notification['status']['content'])

            # bot属性のアカウントの場合は無視する
            if notification['account']['bot'] == True:
                return

            # とりあえずふぁぼる
            print('お手紙っ！：@{0} < {1}'.format(notification['account']['acct'], txt))
            mastodon.status_favourite(notification['status']['id'])

            # 正規表現とか
            followReq = re.search(r'(フォロー|[Ff]ollow|ふぉろー)(して|.?頼(む|みたい|もう)|.?たの(む|みたい|もう)|お願い|おねがい)', txt)

            # メンションでフォローリクエストされたとき
            # (作成途中っ)
            if followReq:
                pass
        
        elif notifyType == 'favourite':
            # ふぁぼられ
            print('ふぁぼられたっ！：@{0}'.format(notification['account']['acct']))
            # 今後好感度とか上げる機能とか入れる
        
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
        memory = KotohiraMemory(showLog=config['log']['enable'])

        # ユウちゃんが知ってるユーザーか調べる
        # 知らない場合はユウちゃんは記憶しますっ！
        isknown = memory.select('known_users', status['account']['id'])
        if len(isknown) == 0:
            now = datetime.datetime.now(timezone('Asia/Tokyo'))
            dt = now.strftime("%Y-%m-%d %H:%M:%S%z")
            memory.insert('known_users', status['account']['id'], status['account']['acct'], dt)
            print('覚えたっ！： @{0}'.format(status['account']['acct']))
            # トゥートカウントが10以下の場合は新規さん向けの挨拶しますっ！
            if status['account']['statuses_count'] <= 10:
                print('新規さん！: @{0}'.format(status['account']['acct']))
                mastodon.status_reblog(status['id'])
                mastodon.toot('新規さんっ！はじめましてっ！琴平ユウって言いますっ！\nよろしくねっ！\n\n@{0}'.format(status['account']['acct']))

        # 正規表現チェック
        calledYuChan = re.search(r'(琴平|ことひら|コトヒラ|ｺﾄﾋﾗ|ゆう|ユウ|ﾕｳ)', txt)
        iBack = re.search(r'(帰宅|ただいま|帰った|帰還)(?!.*(する|します|しちゃう|しよう))', txt)
        passage = re.search(r'(通過|つうか|ツウカ)', txt)
        
        # ユウちゃん etc... とか呼ばれたらふぁぼる
        if calledYuChan:
            print('呼ばれたっ！：@{0} < {1}'.format(status['account']['acct'], txt))
            mastodon.status_favourite(status['id'])

        # 帰ったよ〜 とか言ったらトゥート
        if iBack:
            # データベースからデータ取得
            userInfo = memory.select('known_users', status['account']['id'])[0]
            # タプル型なので6番目のデータが通過阻止した日付
            didWBAt = userInfo[5]
            now = datetime.datetime.now(timezone('Asia/Tokyo'))
            dt = now.strftime("%Y-%m-%d %H:%M:%S%z")
            if didWBAt != None:
                didWBAtRaw = datetime.datetime.strptime(didWBAt, '%Y-%m-%d %H:%M:%S%z')
                dateDiff = now - didWBAtRaw
                # 前回の「通過」etc...から5分以上経過していれば応答する
                if dateDiff.seconds >= 300:
                    doIt = True
                else:
                    doIt = False
            else:
                doIt = True

            if doIt:
                print('おかえりっ！：@{0} < {1}'.format(status['account']['acct'], txt))
                mastodon.toot("""{0}さん、おかえりなさいませっ！""".format(status['account']['display_name']))
                memory.update('known_users-wb', dt, status['account']['id'])

        # 通過 とか言ったら阻止しちゃうよっ！
        if passage:
            userInfo = memory.select('known_users', status['account']['id'])[0]
            # タプル型なので9番目のデータが通過した日付
            didAt = userInfo[8]
            now = datetime.datetime.now(timezone('Asia/Tokyo'))
            dt = now.strftime("%Y-%m-%d %H:%M:%S%z")
            if didAt != None:
                didAtRaw = datetime.datetime.strptime(didAt, '%Y-%m-%d %H:%M:%S%z')
                dateDiff = now - didAtRaw
                # 前回の「ただいま」etc...から10分以上経過していれば応答する
                if dateDiff.seconds >= 600:
                    doIt = True
                else:
                    doIt = False
            else:
                doIt = True
            
            if doIt:
                print('阻止っ！：@{0} < {1}'.format(status['account']['acct'], txt))
                mastodon.toot('阻止っ！！(*`ω´*)')
        else:
            print('@{0} < {1}'.format(status['account']['acct'], txt))

        # データベース切断
        del memory

def local():
    print('Initializing feature: local')
    try:
        mastodon.stream_local(local_listener(), timeout=20)
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
    except:
        KotohiraUtil.PANIC()
        print('ホームタイムラインを五秒待って読み込みし直しますねっ！')
        time.sleep(5)
        home()
