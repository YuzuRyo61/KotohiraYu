from mastodon import Mastodon, StreamListener
import datetime
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
        if notification['type'] == 'mention':
            txt = KotohiraUtil.h2t(notification['status']['content'])

            # bot属性のアカウントの場合は無視する
            if notification['account']['bot'] == True:
                return

            # とりあえずふぁぼる
            print('お手紙っ！：@{0} < {1}'.format(notification['account']['acct'], txt))
            mastodon.status_favourite(notification['status']['id'])

            # 正規表現とか
            followReq = re.search(r'(フォロー|(f|F)ollow|ふぉろー)(して|.?頼(む|みたい|もう)|.?たの(む|みたい|もう)|お願い|おねがい)', txt)

            # メンションでフォローリクエストされたとき
            # (作成途中っ)
            if followReq:
                pass
        else:
            pp.pprint(notification)

# ローカルタイムラインのリスナー
class local_listener(StreamListener):
    def on_update(self, status):
        # Botアカウントは応答しないようにする
        if status['account']['bot'] == True:
            return

        # 自分のトゥートは無視
        if config['user']['me'] == status['account']['acct']:
            return

        # データベース初期化
        memory = KotohiraMemory(showLog=config['log']['enable'])

        # ユウちゃんが知ってるユーザーか調べる
        # 知らない場合はユウちゃんは記憶しますっ！
        isknown = memory.select('known_users', status['account']['id'])
        if len(isknown) == 0:
            now = datetime.datetime.now()
            dt = now.strftime("%Y-%m-%d %H:%M:%S")
            memory.insert('known_users', status['account']['id'], status['account']['acct'], dt)
            print('覚えたっ！： @{0}'.format(status['account']['acct']))
            # トゥートカウントが10以下の場合は新規さん向けの挨拶しますっ！
            if status['account']['statuses_count'] <= 10:
                print('新規さん！: @{0}'.format(status['account']['acct']))
                mastodon.toot('新規さんっ！はじめましてっ！ユウって言いますっ！\nよろしくねっ！\n\n@{0}'.format(status['account']['acct']))

        # トゥート内のHTMLタグを除去
        txt = KotohiraUtil.h2t(status['content'])

        # 正規表現チェック
        isMeMention = re.search('@{}'.format(config['user']['me']), txt)
        calledYuChan = re.search(r'(琴平|ことひら|コトヒラ|ｺﾄﾋﾗ|ゆう|ユウ|ﾕｳ)', txt)
        iBack = re.search(r'(帰宅|ただいま|帰った|帰還)(?!.*(する|します|しちゃう|しよう))', txt)

        # 自分宛てのメンションはここのリスナーでは無視する
        if isMeMention:
            return
        
        # ユウちゃん etc... とか呼ばれたらふぁぼる
        if calledYuChan:
            print('呼ばれたっ！：@{0} < {1}'.format(status['account']['acct'], txt))
            mastodon.status_favourite(status['id'])

        # 帰ったよ〜 とか言ったらトゥート
        if iBack:
            print('おかえりっ！：@{0} < {1}'.format(status['account']['acct'], txt))
            mastodon.toot("""{0}さん、おかえりなさいませっ！""".format(status['account']['display_name']))
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