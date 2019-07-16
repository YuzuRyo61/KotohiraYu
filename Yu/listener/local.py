# -*- coding: utf-8 -*-
import configparser
import datetime
import random
import re
import time

from mastodon import Mastodon, StreamListener
from pytz import timezone

from Yu import KotohiraMemory, KotohiraUtil, YuChan

config = configparser.ConfigParser()
config.read('config/config.ini')

mastodon = Mastodon(
    access_token='config/accesstoken.txt',
    api_base_url=config['instance']['address']
)

# ローカルタイムラインのリスナー
class local_listener(StreamListener):
    def on_update(self, status):
        try:
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

            # NGワードを検知した場合は弾いて好感度下げ
            if YuChan.ngWordHook(txt):
                print('変なことを言ってはいけませんっ！！(*`ω´*): @{0}'.format(status['account']['acct']))
                memory.update('fav_rate', -10, status['account']['id'])
                YuChan.unfollow_attempt(status['account']['id'])
                return

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
            otherNick = re.search(r':@([a-zA-Z0-9_]+):\sの(あだ名|あだな|ニックネーム)[:：は]\s?(.+)', txt)
            nick = re.search(r'^(あだ(名|な)|ニックネーム)[:：は]\s?', txt)
            iBack = re.search(r'(帰宅|ただいま|帰った|帰還)(?!.*(する|します|しちゃう|しよう|中|ちゅう|してる))', txt)
            goodNight = re.search(r'寝(ます|る|マス)([よかぞね]?|[...。うぅー~!・]+)$|^寝(ます|る|よ)[...。うぅー~!・]*$|寝(ます|る|マス)(.*)[ぽお]や[ユすしー]|(ユウ|ﾕｳ|ゆう|ことひら|コトヒラ|ｺﾄﾋﾗ)(ちゃん)?(.*)[ぽお]や[ユすしー]', txt)
            seeYou = re.search(r'((行|い)って(きます|くる)|ノシ|ﾉｼ)', txt)
            passage = re.search(r'(通過|つうか|ツウカ)(?!.*(おめ|した))', txt)
            sinkiSagi = re.search(r'(新規|しんき)(です|だよ|なのじゃ)', txt)
            nullPoint = re.search(r'(ぬるぽ|ヌルポ|ﾇﾙﾎﾟ|[nN][uU][lL]{2}[pP][oO])', txt)
            notNicoFri = re.search(r'(にこふれ|ニコフレ|ﾆｺﾌﾚ)', txt)
            sad = re.search(r'((泣|な)いてる|しくしく|シクシク|ｼｸｼｸ|ぐすん|グスン|ｸﾞｽﾝ|ぶわっ|ブワッ|ﾌﾞﾜｯ)', txt)
            noNow = re.search(r'(いまのなし|イマノナシ|ｲﾏﾉﾅｼ)', txt)
            writeDict = re.search(r'^:@[a-zA-Z0-9_]+:(さん|くん|君|殿|どの|ちゃん)?はこんな人[:：]', txt)
            writeMemo = re.search(r'^(メモ|めも|[Mm][Ee][Mm][Oo])[:：]', txt)
            
            # ユウちゃん etc... とか呼ばれたらふぁぼる
            if calledYuChan:
                print('呼ばれたっ！：@{0} < {1}'.format(status['account']['acct'], txt))
                mastodon.status_favourite(status['id'])
                # 好感度ちょいアップ
                memory.update('fav_rate', 1, status['account']['id'])

            # 投票型のトゥートだったら投票する（期限切れでないかつ投票してないこと）
            if status['poll'] != None:
                if status['poll']['expired'] == False and not ('voted' in status['poll'] and status['poll']['voted'] == True):
                    # ここで投票する場所を抽選
                    voteOptions = status['poll']['options']
                    
                    # NGワードを検知した場合は弾いて好感度下げ
                    for voteSection in voteOptions:
                        if YuChan.ngWordHook(voteSection['title']):
                            print('変なことを言ってはいけませんっ！！(*`ω´*): @{0}'.format(status['account']['acct']))
                            memory.update('fav_rate', -10, status['account']['id'])
                            return
                    
                    voteChoose = random.randint(0, len(voteOptions) - 1)
                    mastodon.poll_vote(status['poll']['id'], voteChoose)
                    # 投票したものをトゥートする
                    print('投票っ！：@{0} => {1}'.format(status['account']['acct'], status['poll']['options'][voteChoose]['title']))
                    mastodon.status_post('ユウちゃんは「{0}」がいいと思いますっ！\n\n{1}'.format(status['poll']['options'][voteChoose]['title'], status['url']))

            elif otherNick:
                # 他人のニックネームの設定
                YuChan.set_otherNickname(txt, status['id'], status['account']['id'], status['account']['acct'], status['visibility'], memory)

            elif nick:
                # ニックネームの設定
                YuChan.set_nickname(txt, status['id'], status['account']['id'], status['account']['acct'], status['visibility'], memory)

            elif iBack:
                # おかえりとか言ったら実行
                if YuChan.msg_hook('wel_back', 600, ":@{0}: {1}さん、おかえりなさいませっ！".format(status['account']['acct'], name), status, memory):
                    print('おかえりっ！：@{0} < {1}'.format(status['account']['acct'], txt))

            elif goodNight:
                # おやすみですっ！
                if YuChan.msg_hook('good_night', 600, ":@{0}: {1}さん、おやすみなさいっ！🌙".format(status['account']['acct'], name), status, memory):
                    print('おやすみっ！:@{0} < {1}'.format(status['account']['acct'], txt))

            elif seeYou:
                # いってらっしゃいなのですっ！
                if YuChan.msg_hook('see_you', 600, ":@{0}: {1}さん、いってらっしゃいっ！🚪".format(status['account']['acct'], name), status, memory):
                    print('いってらっしゃいっ！:@{0} < {1}'.format(status['account']['acct'], txt))                

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
                if YuChan.msg_hook('null_point', 180, ":gaxtsu:", status, memory):
                    print('がっ：@{0} < {1}'.format(status['account']['acct'], txt))

            elif notNicoFri:
                # ニコフレじゃないよっ！
                if YuChan.msg_hook('not_nikofure', 10800, "ここはニコフレじゃないですっ！！ベスフレですっ！(*`ω´*)", status, memory):
                    print('ベスフレですっ！：@{0} < {1}'.format(status['account']['acct'], txt))

            elif sad:
                # よしよしっ
                if YuChan.msg_hook('yoshiyoshi', 180, "(´･ω･`)ヾ(･ω･｡)ﾖｼﾖｼ", status, memory):
                    print('よしよしっ：@{0} < {1}'.format(status['account']['acct'], txt))

            elif noNow:
                # いまのなしは封印ですっ！
                if YuChan.msg_hook('no_now', 180, "いまのなしは封印ですっ！！(*`ω´*)", status, memory):
                    print('いまのなしは封印ですっ！：@{0} < {1}'.format(status['account']['acct'], txt))

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
                res = YuChan.write_memo(status['account']['acct'], memoBody, status['id'], memory)
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
                    # 名前に語尾がない場合は付け足す
                    if len(re.findall(r'(さん|ちゃん|どの|殿|くん|君|様|さま|教授|たん|きゅん)$', name)) == 0:
                        name += "さん"
                    time.sleep(0.5)
                    if now.hour < 12 and now.hour >= 5:
                        print("おはようございますっ！：@{0} < {1}".format(status['account']['acct'], txt))
                        mastodon.toot(""":@{1}: {0}、おはようございますっ！🌄""".format(name, status['account']['acct']))
                    elif now.hour >= 12 and now.hour < 17:
                        print("こんにちはっ！：@{0} < {1}".format(status['account']['acct'], txt))
                        mastodon.toot(""":@{1}: {0}、こんにちはっ！☀""".format(name, status['account']['acct']))
                    elif now.hour >= 17 and now.hour < 5:
                        print("こんばんはっ！：@{0} < {1}".format(status['account']['acct'], txt))
                        mastodon.toot(""":@{1}: {0}、こんばんはっ！🌙""".format(name, status['account']['acct']))

                # 最終更新を変更
                memory.update('updated_users', dt, status['account']['id'])

        except Exception as e:
            raise e # Timelines.pyの方へエラーを送出させる
        finally: # 必ず実行
            try:
                del memory # データベースロック防止策、コミットする
            except NameError: # 定義されていなくてもエラーを出さない
                pass

    def on_delete(self, status_id):
        try:
            # メモのトゥートが削除されたらデータベースから削除する
            if YuChan.cancel_memo(status_id):
                print(f"メモを削除っ！: {str(status_id)}")
        except Exception as e: # 上と同じ
            raise e
        finally:
            try:
                del memory
            except NameError:
                pass
