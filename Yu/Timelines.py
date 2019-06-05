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

from Yu import KotohiraUtil, KotohiraMemory, YuChan

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
            followReq = re.search(r'(フォロー|[Ff]ollow|ふぉろー)(して|.?頼(む|みたい|もう)|.?たの(む|みたい|もう)|お願い|おねがい)?', txt)
            fortune = re.search(r'(占|うらな)(って|い)', txt)
            nick = re.search(r'(あだ(名|な)|ニックネーム)[:：は]\s?', txt)
            deleteNick = re.search(r'(ニックネーム|あだ名)を?(消して|削除|けして|さくじょ)', txt)
            rspOtt = re.search(r'じゃんけん\s?(グー|✊|👊|チョキ|✌|パー|✋)', txt)
            isPing = re.search(r'[pP][iI][nN][gG]', txt)

            # メンションでフォローリクエストされたとき
            if followReq:
                reqRela = mastodon.account_relationships(notification['account']['id'])[0]
                # フォローしていないこと
                if reqRela['following'] == False:
                    if reqRela['followed_by'] == True: # フォローされていること
                        reqMem = memory.select('fav_rate', notification['account']['id'])[0]
                        if int(reqMem[2]) >= 200: # 200以上だったら合格
                            print('フォローっ！：@{}'.format(notification['account']['acct']))
                            mastodon.account_follow(notification['account']['id'])
                            mastodon.status_post('@{}\nフォローしましたっ！これからもよろしくねっ！'.format(notification['account']['acct']), in_reply_to_id=notification['status']['id'], visibility=notification['status']['visibility'])
                        else: # 不合格の場合はレスポンスして終了
                            print('もうちょっと仲良くなってからっ！：@{}'.format(notification['account']['acct']))
                            mastodon.status_post('@{}\nもうちょっと仲良くなってからですっ！'.format(notification['account']['acct']), in_reply_to_id=notification['status']['id'], visibility=notification['status']['visibility'])
                    else:
                        print('先にフォローしてっ！:@{}'.format(notification['account']['acct']))
                        mastodon.status_post('@{}\nユウちゃんをフォローしてくれたら考えますっ！'.format(notification['account']['acct']), in_reply_to_id=notification['status']['id'], visibility=notification['status']['visibility'])
                else: # フォローしている場合は省く
                    print('フォロー済みっ！：@{}'.format(notification['account']['acct']))
                    mastodon.status_post('@{}\nもうフォローしてますっ！'.format(notification['account']['acct']), in_reply_to_id=notification['status']['id'], visibility=notification['status']['visibility'])
            
            # 占いのリクエストがされたとき
            elif fortune:
                YuChan.fortune(notification['status']['id'], notification['account']['acct'], notification['status']['visibility'])
                # 更に４つ加算
                memory.update('fav_rate', 4, notification['account']['id'])

            # ニックネームの削除
            elif deleteNick:
                YuChan.del_nickname(notification['status']['id'], notification['account']['id'], notification['account']['acct'], notification['status']['visibility'], memory)

            # ニックネームの設定
            elif nick:
                YuChan.set_nickname(txt, notification['status']['id'], notification['account']['id'], notification['account']['acct'], notification['status']['visibility'], memory)

            # ユウちゃんとじゃんけんっ！
            elif rspOtt:
                YuChan.rsp(txt, notification)
                # 更に４つ加算
                memory.update('fav_rate', 4, notification['account']['id'])

            # 応答チェッカー
            elif isPing:
                print('PINGっ！：@{}'.format(notification['account']['acct']))
                mastodon.status_post('@{}\nPONG!'.format(notification['account']['acct']), in_reply_to_id=notification['status']['id'], visibility=notification['status']['visibility'])

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

        # 自分宛てのメンションはここのリスナーでは無視する（ユーザー絵文字の場合は例外）
        isMeMention = re.search('(?!.*(:))@{}(?!.*(:))'.format(config['user']['me']), txt)
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
                time.sleep(0.5)
                mastodon.toot('新規さんっ！はじめましてっ！琴平ユウって言いますっ！\nよろしくねっ！\n\n:@{0}: @{0}'.format(status['account']['acct']))
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
                # デコードして、\u202e(文字が逆さまになるやつ)を削除して戻してどーん
                dpname = status['account']['display_name'].encode('unicode-escape')
                dpname = dpname.replace(b"\\u202e", b'')
                name = dpname.decode('unicode-escape')
        else:
            # ニックネームが設定されている場合はそちらを優先
            name = nameDic[0][2]
        # ユーザー絵文字や半角@を除去（こうするしかなかった）
        name = re.sub(r'[:]?@\w*[:]?', '', name)

        # 正規表現チェック
        calledYuChan = re.search(r'(琴平|ことひら|コトヒラ|ｺﾄﾋﾗ|ゆう|ゆぅ|ユウ|ユゥ|ﾕｳ|ﾕｩ|:@' + config['user']['me'] + ':)', txt)
        iBack = re.search(r'(帰宅|ただいま|帰った|帰還)(?!.*(する|します|しちゃう|しよう|中|ちゅう|してる))', txt)
        passage = re.search(r'(通過|つうか|ツウカ)(?!.*(おめ|した))', txt)
        sinkiSagi = re.search(r'(新規|しんき)(です|だよ|なのじゃ)', txt)
        nullPoint = re.search(r'(ぬるぽ|ヌルポ|ﾇﾙﾎﾟ|[nN][uU][lL]{2}[pP][oO])', txt)
        notNicoFri = re.search(r'(にこふれ|ニコフレ|ﾆｺﾌﾚ)', txt)
        sad = re.search(r'((泣|な)いてる|しくしく|シクシク|ｼｸｼｸ|ぐすん|グスン|ｸﾞｽﾝ|ぶわっ|ブワッ|ﾌﾞﾜｯ)', txt)
        nick = re.search(r'^(あだ(名|な)|ニックネーム)[:：は]\s?', txt)
        writeDict = re.search(r'^:@[a-zA-Z0-9_]+:(さん|くん|君|殿|どの|ちゃん)?はこんな人[:：]', txt)
        writeMemo = re.search(r'^(メモ|めも|[Mm][Ee][Mm][Oo])[:：]', txt)
        
        # ユウちゃん etc... とか呼ばれたらふぁぼる
        if calledYuChan:
            print('呼ばれたっ！：@{0} < {1}'.format(status['account']['acct'], txt))
            mastodon.status_favourite(status['id'])
            # 好感度ちょいアップ
            memory.update('fav_rate', 1, status['account']['id'])

        # 投票型のトゥートだったら投票する（期限切れでないかつ投票してないこと）
        # issue: #5
        if status['poll'] != None:
            if status['poll']['expired'] == False and not ('voted' in status['poll'] and status['poll']['voted'] == True):
                # ここで投票する場所を抽選
                voteOptions = status['poll']['options']
                voteChoose = random.randint(0, len(voteOptions) - 1)
                mastodon.poll_vote(status['poll']['id'], voteChoose)
                # 投票したものをトゥートする
                print('投票っ！：@{0} => {1}'.format(status['account']['acct'], status['poll']['options'][voteChoose]['title']))
                mastodon.status_post('ユウちゃんは「{0}」がいいと思いますっ！\n\n{1}'.format(status['poll']['options'][voteChoose]['title'], status['url']))

        if iBack:
            # おかえりとか言ったら実行
            if YuChan.msg_hook('wel_back', 600, ":@{0}: {1}さん、おかえりなさいませっ！".format(status['account']['acct'], name), status, memory):
                print('おかえりっ！：@{0} < {1}'.format(status['account']['acct'], txt))

        elif passage:
            # 通過 とか言ったら阻止しちゃうよっ！
            if YuChan.msg_hook('passage', 300, "阻止っ！！(*`ω´*)", status, memory):
                print('阻止っ！：@{0} < {1}'.format(status['account']['acct'], txt))

        elif sinkiSagi and status['account']['statuses_count'] > 10:
            # 新規詐欺見破りっ！            
            if YuChan.msg_hook('sin_sagi', 10800, "新規詐欺はいけませんっ！！(*`ω´*)", status, memory):
                print('新規詐欺っ！:@{0} < {1}'.format(status['account']['acct'], txt))
        
        elif nullPoint:
            # ぬるぽって、言ったら■━⊂( ･∀･)彡ｶﾞｯ☆`Дﾟ)
            if YuChan.msg_hook('null_point', 180, "ｶﾞｯ", status, memory):
                print('がっ：@{0} < {1}'.format(status['account']['acct'], txt))

        elif notNicoFri:
            # ニコフレじゃないよっ！
            if YuChan.msg_hook('not_nikofure', 10800, "ここはニコフレじゃないですっ！！ベスフレですっ！(*`ω´*)", status, memory):
                print('ベスフレですっ！：@{0} < {1}'.format(status['account']['acct'], txt))

        elif sad:
            # よしよしっ
            if YuChan.msg_hook('yoshiyoshi', 180, "(´･ω･`)ヾ(･ω･｡)ﾖｼﾖｼ", status, memory):
                print('よしよしっ：@{0} < {1}'.format(status['account']['acct'], txt))

        elif nick:
            # ニックネームの設定
            YuChan.set_nickname(txt, status['id'], status['account']['id'], status['account']['acct'], status['visibility'], memory)

        elif writeDict:
            # 辞書登録っ
            # (実装中)
            # YuChan.update_userdict()
            pass
        
        elif writeMemo:
            # メモの書き込みっ
            memoBody = re.sub(r'^(メモ|めも|[Mm][Ee][Mm][Oo])[:：]', '', txt, 1)
            mastodon.status_reblog(status['id'])
            print('メモっ！：@{0} < {1}'.format(status['account']['acct'], txt))
            res = YuChan.write_memo(status['account']['acct'], memoBody, memory)
            if res == False:
                mastodon.status_post('@{}\n長いのでまとめられそうにありませんっ・・・'.format(status['account']['acct']), in_reply_to_id=status['id'])

        # 最終更新を変更
        now = datetime.datetime.now(timezone('Asia/Tokyo'))
        dt = now.strftime("%Y-%m-%d %H:%M:%S%z")
        # ２重更新防策
        if not newUser:
            updated_at = memory.select('updated_users', status['account']['id'])[0]
            updatedAtRaw = datetime.datetime.strptime(updated_at[2], '%Y-%m-%d %H:%M:%S%z')
            greetableTime = updatedAtRaw + datetime.timedelta(hours=3)
            shouldGreet = now >= greetableTime
            # 3時間以上更新がなかった場合は挨拶する
            if shouldGreet:
                time.sleep(0.5)
                if now.hour < 12 and now.hour >= 5:
                    print("おはようございますっ！：@{0} < {1}".format(status['account']['acct'], txt))
                    mastodon.toot(""":@{1}: {0}さん、おはようございますっ！🌄""".format(name, status['account']['acct']))
                if now.hour >= 12 and now.hour < 17:
                    print("こんにちはっ！：@{0} < {1}".format(status['account']['acct'], txt))
                    mastodon.toot(""":@{1}: {0}さん、こんにちはっ！☀""".format(name, status['account']['acct']))
                if now.hour >= 17 and now.hour < 5:
                    print("こんばんはっ！：@{0} < {1}".format(status['account']['acct'], txt))
                    mastodon.toot(""":@{1}: {0}さん、こんばんはっ！🌙""".format(name, status['account']['acct']))

            # 最終更新を変更
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
        home()
    except (requests.exceptions.ReadTimeout, MastodonNetworkError):
        print('＊ホームタイムラインが繋がんないみたいですっ・・・。１分後にやり直しますっ！')
        time.sleep(60)
        home()
    except:
        KotohiraUtil.PANIC()
        print('ホームタイムラインを十秒待って読み込みし直しますねっ！')
        time.sleep(10)
        home()
