from mastodon import Mastodon, StreamListener, MastodonNetworkError
from sqlite3 import OperationalError
import datetime
import random
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
            deleteNick = re.search(r'(ニックネーム|あだ名)を?(消して|削除|けして|さくじょ)', txt)
            rspOtt = re.search(r'じゃんけん\s?(グー|✊|👊|チョキ|✌|パー|✋)', txt)

            # メンションでフォローリクエストされたとき
            # (作成途中っ)
            if followReq:
                pass
            
            # 占いのリクエストがされたとき
            elif fortune:
                Yu.fortune(notification['status']['id'], notification['account']['acct'])
                # 更に４つ加算
                memory.update('fav_rate', 4, notification['account']['id'])
            
            elif deleteNick:
                isexistname = memory.select('nickname', notification['account']['id'])
                if len(isexistname) != 0:
                    memory.delete('nickname', notification['account']['id'])
                    print('ニックネーム削除っ！：@{}'.format(notification['account']['acct']))
                    mastodon.status_post('@{}\nわかりましたっ！今度から普通に呼ばせていただきますっ！'.format(notification['account']['acct']), in_reply_to_id=notification['status']['id'])
                else:
                    print('ニックネームを登録した覚えがないよぉ・・・：@{}'.format(notification['account']['acct']))
                    mastodon.status_post('@{}\nあれれ、ニックネームを登録した覚えがありませんっ・・・。'.format(notification['account']['acct']), in_reply_to_id=notification['status']['id'])

            # ユウちゃんとじゃんけんっ！
            elif rspOtt:
                # 選択項目チェック
                ott = re.sub(r'じゃんけん\s?', '', txt, 1)
                # グー
                rock = re.search(r'(グー|✊|👊)', ott)
                # チョキ
                scissors = re.search(r'(チョキ|✌)', ott)
                # パー
                papers = re.search(r'(パー|✋)', ott)

                # 抽選っ！
                yuOttChoose = random.randint(0, 2)

                # 抽選した数値で絵文字にパースする
                if yuOttChoose == 0:
                    yuOttChooseEmoji = "✊"
                elif yuOttChoose == 1:
                    yuOttChooseEmoji = "✌"
                elif yuOttChoose == 2:
                    yuOttChooseEmoji = "✋"

                # 挑戦者が勝ちかどうかの判別変数。勝ちはTrue、負けはFalse、あいこはNoneとする
                isChallengerWin = None
                challengerChoose = None

                if rock:
                    print("じゃんけんっ！：@{0} => ✊ vs {1}".format(notification['account']['acct'], yuOttChooseEmoji))
                    challengerChoose = "✊"
                    if yuOttChoose == 0:
                        isChallengerWin = None
                    elif yuOttChoose == 1:
                        isChallengerWin = True
                    elif yuOttChoose == 2:
                        isChallengerWin = False
                elif scissors:
                    print("じゃんけんっ！：@{0} => ✌ vs {1}".format(notification['account']['acct'], yuOttChooseEmoji))
                    challengerChoose = "✌"
                    if yuOttChoose == 0:
                        isChallengerWin = False
                    elif yuOttChoose == 1:
                        isChallengerWin = None
                    elif yuOttChoose == 2:
                        isChallengerWin = True
                elif papers:
                    print("じゃんけんっ！：@{0} => ✋ vs {1}".format(notification['account']['acct'], yuOttChooseEmoji))
                    challengerChoose = "✋"
                    if yuOttChoose == 0:
                        isChallengerWin = True
                    elif yuOttChoose == 1:
                        isChallengerWin = False
                    elif yuOttChoose == 2:
                        isChallengerWin = None

                if isChallengerWin == True:
                    mastodon.status_post('@{0}\nあなた：{1}\nユウちゃん：{2}\n🎉 あなたの勝ちですっ！！'.format(notification['account']['acct'], challengerChoose, yuOttChooseEmoji), in_reply_to_id=notification['status']['id'])
                elif isChallengerWin == None:
                    mastodon.status_post('@{0}\nあなた：{1}\nユウちゃん：{2}\n👍 あいこですっ'.format(notification['account']['acct'], challengerChoose, yuOttChooseEmoji), in_reply_to_id=notification['status']['id'])
                elif isChallengerWin == False:
                    mastodon.status_post('@{0}\nあなた：{1}\nユウちゃん：{2}\n👏 ユウちゃんの勝ちですっ！'.format(notification['account']['acct'], challengerChoose, yuOttChooseEmoji), in_reply_to_id=notification['status']['id'])
                
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

        # 名前
        nameDic = memory.select('nickname', status['account']['id'])
        if len(nameDic) == 0:
            # ニックネームが指定されていない場合は基の名前を使用する
            # 名前が設定されていない場合はユーザーIDを使用する
            if status['account']['display_name'] == '':
                name = status['account']['acct']
            else:
                # Unicodeのエスケープを削除して挿入
                dpname = repr(status['account']['display_name'])[1:-1]
                name = re.sub(r"\\u[0-9a-f]{4}", '', dpname)
        else:
            # ニックネームが設定されている場合はそちらを優先
            name = nameDic[0][2]

        # 正規表現チェック
        calledYuChan = re.search(r'(琴平|ことひら|コトヒラ|ｺﾄﾋﾗ|ゆう|ゆぅ|ユウ|ユゥ|ﾕｳ|ﾕｩ)', txt)
        iBack = re.search(r'(帰宅|ただいま|帰った|帰還)(?!.*(する|します|しちゃう|しよう|中|ちゅう))', txt)
        passage = re.search(r'(通過|つうか|ツウカ)(?!.*(おめ|した))', txt)
        sinkiSagi = re.search(r'(新規|しんき)(です|だよ|なのじゃ)', txt)
        nullPoint = re.search(r'(ぬるぽ|ヌルポ|ﾇﾙﾎﾟ|[nN][uU][lL]{2}[pP][oO])', txt)
        nick = re.search(r'^(あだ(名|な)|ニックネーム)[:：は]?\s?', txt)
        
        # ユウちゃん etc... とか呼ばれたらふぁぼる
        if calledYuChan:
            print('呼ばれたっ！：@{0} < {1}'.format(status['account']['acct'], txt))
            mastodon.status_favourite(status['id'])
            # 好感度ちょいアップ
            memory.update('fav_rate', 1, status['account']['id'])

        # 投票型のトゥートだったら投票する（期限切れでないかつ投票してないこと）
        # issue: #5
        # Mastodon.pyで未検証みたいなのでしばらく見送り
        """
        if status['poll'] != None:
            if status['poll']['expired'] == False and status['poll']['voted'] == False:
                # ここで投票する場所を抽選
                voteOptions = status['poll']['options']
                voteChoose = random.randint(0, len(voteOptions) - 1)
                mastodon.poll_vote(status['id'], voteChoose)
        """

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
                mastodon.toot("""{0}さん、おかえりなさいませっ！""".format(name))
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
        
        # 新規詐欺見破りっ！
        if sinkiSagi and status['account']['statuses_count'] > 10:
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
                mastodon.toot('新規詐欺はいけませんっ！！(*`ω´*)')
                memory.update('sin_sagi', status['account']['id'], dt)
        
        # ぬるぽって、言ったら■━⊂( ･∀･)彡ｶﾞｯ☆`Дﾟ)
        if nullPoint:
            userInfo = memory.select('null_point', status['account']['id'])
            now = datetime.datetime.now(timezone('Asia/Tokyo'))
            dt = now.strftime("%Y-%m-%d %H:%M:%S%z")
            if len(userInfo) == 0:
                # データがない場合はデータ挿入してガッ実行
                memory.insert('null_point', status['account']['id'], dt)
                doIt = True
            else:
                didAt = userInfo[0][2]
                didAtRaw = datetime.datetime.strptime(didAt, '%Y-%m-%d %H:%M:%S%z')
                dateDiff = now - didAtRaw
                # 前回の詐欺の「ぬるぽ」etc...から3分以上経過していれば応答する
                if dateDiff.seconds >= 180:
                    doIt = True
                else:
                    doIt = False
            
            if doIt:
                print('がっ：@{0} < {1}'.format(status['account']['acct'], txt))
                mastodon.toot('ｶﾞｯ')
                memory.update('null_point', status['account']['id'], dt)

        # ニックネームの設定
        if nick:
            userInfo = memory.select('nickname', status['account']['id'])
            name = re.sub(r'^(あだ(名|な)|ニックネーム)[:：は]?\s?', '', txt, 1)
            name = name.replace('\n', '')
            if len(userInfo) == 0:
                memory.insert('nickname', status['account']['id'], name)
            else:
                memory.update('nickname', name, status['account']['id'])
            # 変更通知
            print('ニックネーム変更っ！：@{0} => {1}'.format(status['account']['acct'], name))
            mastodon.status_post('@{0}\nわかりましたっ！今度から\n「{1}」と呼びますねっ！'.format(status['account']['acct'], name), in_reply_to_id=status['id'])

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
                if now.hour < 12 and now.hour >= 5:
                    print("おはようございますっ！：@{0} < {1}".format(status['account']['acct'], txt))
                    mastodon.toot("""{0}さん、おはようございますっ！🌄""".format(name))
                if now.hour >= 12 and now.hour < 17:
                    print("こんにちはっ！：@{0} < {1}".format(status['account']['acct'], txt))
                    mastodon.toot("""{0}さん、こんにちはっ！☀""".format(name))
                if now.hour >= 17 and now.hour < 5:
                    print("こんばんはっ！：@{0} < {1}".format(status['account']['acct'], txt))
                    mastodon.toot("""{0}さん、こんばんはっ！🌙""".format(name))

            memory.update('updated_users', dt, status['account']['id'])

        # データベース切断
        del memory

def local():
    print('Initializing feature: local')
    try:
        mastodon.stream_local(local_listener(), timeout=20)
    except OperationalError:
        print('＊データベースにアクセスできないか、エラーが起きたようですっ。３０秒後にやり直しますっ！')
        time.sleep(30)
        local()
    except (requests.exceptions.ReadTimeout, MastodonNetworkError):
        print('＊ローカルタイムラインが繋がんないみたいですっ・・・。１分後にやり直しますっ！')
        time.sleep(60)
        local()
    except:
        KotohiraUtil.PANIC()
        print('ローカルタイムラインを十秒待って読み込みし直しますねっ！')
        time.sleep(10)
        local()

def home():
    print('Initializing feature: home')
    print('Connect address: {}'.format(config['instance']['address']))
    try:
        res = mastodon.account_verify_credentials()
        print('Fetched account: @{}'.format(res.acct))
        mastodon.stream_user(user_listener(), timeout=20)
    except OperationalError:
        print('＊データベースにアクセスできないか、エラーが起きたようですっ。３０秒後にやり直しますっ！')
        time.sleep(30)
        local()
    except (requests.exceptions.ReadTimeout, MastodonNetworkError):
        print('＊ホームタイムラインが繋がんないみたいですっ・・・。１分後にやり直しますっ！')
        time.sleep(60)
        home()
    except:
        KotohiraUtil.PANIC()
        print('ホームタイムラインを十秒待って読み込みし直しますねっ！')
        time.sleep(10)
        home()
