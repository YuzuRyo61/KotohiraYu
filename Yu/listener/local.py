import configparser
import datetime
import random
import re
import time
import threading

from mastodon import StreamListener
from pytz import timezone, utc
from dateutil import parser as duParser

from Yu import YuChan, Util as KotohiraUtil, log
from Yu.config import config
from Yu.mastodon import mastodon
from Yu.database import DATABASE
from Yu.models import known_users, nickname, updated_users, fav_rate

# 投票再通知用スレッド辞書
VOTE_RENOTIFY_THREAD = {}

# ローカルタイムラインのリスナー
def local_onUpdate(status):
    try:
        with DATABASE.transaction():
            # Botアカウントは応答しないようにする
            if status['account']['bot'] == True:
                return

            # 自分のトゥートは無視
            if config['user']['me'] == status['account']['acct']:
                return

            # トゥート内のHTMLタグを除去
            txt = KotohiraUtil.h2t(status['content'])

            # CWのテキストが空っぽでなければ付け足す
            if status['spoiler_text'] != '':
                txt = status['spoiler_text'] + "\n\n" + txt
                txt.strip()

            # 自分宛てのメンションはここのリスナーでは無視する（ユーザー絵文字の場合は例外）
            isMeMention = re.search('(?!.*:)@({}+)(?!.*:)'.format(config['user']['me']), txt)
            if isMeMention:
                return

            # ユウちゃんが知ってるユーザーか調べる
            # 知らない場合はユウちゃんは記憶しますっ！
            user = known_users.get_or_none(known_users.ID_Inst == int(status['account']['id']))
            if user == None:
                user = known_users.create(ID_Inst=int(status['account']['id']), acct=status['account']['acct'])
                fav_rate.create(ID_Inst=user)
                updated_users.create(ID_Inst=user)
                log.logInfo(f'覚えたっ！： @{status["account"]["acct"]}')
                newUser = True
                # トゥートカウントが10以下で、設定で有効な場合は新規さん向けの挨拶しますっ！
                if status['account']['statuses_count'] <= 10 and config['features']['newComerGreeting'] == True:
                    log.logInfo(f'新規さん！: @{status["account"]["acct"]}')
                    mastodon.status_reblog(status['id'])
                    time.sleep(0.5)
                    mastodon.toot('新規さんっ！はじめましてっ！琴平ユウって言いますっ！\nよろしくねっ！\n\n:@{0}: @{0}'.format(status['account']['acct']))
            else:
                newUser = False

            # NGワードを検知した場合は弾いて好感度下げ
            if YuChan.ngWordHook(txt):
                log.logInfo('変なことを言ってはいけませんっ！！(*`ω´*): @{0}'.format(status['account']['acct']))
                hooked = fav_rate.get(fav_rate.ID_Inst == user)
                hooked.rate -= config['follow']['down_step']
                hooked.save()
                YuChan.unfollow_attempt(status['account']['id'])
                return

            # 名前
            nameDic = nickname.get_or_none(nickname.ID_Inst == user)
            if nameDic == None:
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
                name = nameDic.nickname
            name = re.sub(r'(?!.*:)@([a-zA-Z0-9_]+)(?!.*:)', '', name)
            name = re.sub(r'(.*):$', r'\g<1>: ', name)

            # 名前に語尾がない場合は付け足す
            if re.search(r'(さん|ちゃん|どの|殿|くん|君|様|さま|教授|たん|きゅん)$', name) == None:
                name += "さん"

            # 最終更新を変更
            now = datetime.datetime.now()

            # 正規表現チェック
            calledYuChan = re.search(f'(琴平|ことひら|コトヒラ|ｺﾄﾋﾗ|:@{config["user"]["me"]}:|((ゆう|ユウ|ユゥ|ﾕｳ|ﾕｩ)(ちゃん|チャン|ﾁｬﾝ|くん|クン|君|ｸﾝ))|ユウ)', txt)
            otherNick = re.search(r'^:@([a-zA-Z0-9_]+):\sの(あだ名|あだな|ニックネーム)[:：は]\s?(.+)', txt)
            nick = re.search(r'^(あだ(名|な)|ニックネーム)[:：は]\s?(.+)', txt)
            iBack = re.search(r'(帰宅|ただいま|帰った|帰還)(?!.*(する|します|しちゃう|しよう|中|ちゅう|してる))', txt)
            goodNight = re.search(r'寝(ます|る|マス)([よかぞね]?|[...。うぅー~!・]+)$|^寝(ます|る|よ)[...。うぅー~!・]*$|寝(ます|る|マス)(.*)[ぽお]や[ユすしー]|(ユウ|ﾕｳ|ゆう|ことひら|コトヒラ|ｺﾄﾋﾗ)(ちゃん)?(.*)[ぽお]や[ユすしー]|^(\s*:shushin:\s*)+$', txt)
            seeYou = re.search(r'((行|い)って(きます|くる)|ノシ|ﾉｼ)', txt)
            passage = re.search(r'(通過|つうか|ツウカ)(?!.*(おめ|した))', txt)
            sinkiSagi = re.search(r'(新規|しんき)(です|だよ|なのじゃ)', txt)
            nullPoint = re.search(r'(ぬるぽ|ヌルポ|ﾇﾙﾎﾟ|[nN][uU][lL]{2}[pP][oO])', txt)
            notNicoFri = re.search(r'(にこふれ|ニコフレ|ﾆｺﾌﾚ)', txt)
            sad = re.search(r'((泣|な)いてる|しくしく|シクシク|ｼｸｼｸ|ぐすん|グスン|ｸﾞｽﾝ|ぶわっ|ブワッ|ﾌﾞﾜｯ)', txt)
            noNow = re.search(r'(いまのなし|イマノナシ|ｲﾏﾉﾅｼ)', txt)
            writeDict = re.search(r'^:@[a-zA-Z0-9_]+:(さん|くん|君|殿|どの|ちゃん)?はこんな人[:：]', txt)
            writeMemo = re.search(r'^(メモ|めも|[Mm][Ee][Mm][Oo])[:：](.+)', txt)
            
            # ユウちゃん etc... とか呼ばれたらふぁぼる
            if calledYuChan:
                log.logInfo('呼ばれたっ！：@{0} < {1}'.format(status['account']['acct'], txt))
                mastodon.status_favourite(status['id'])
                # 好感度ちょいアップ
                fav = fav_rate.get(fav_rate.ID_Inst == user)
                fav.rate += 5
                fav.save()

            # 投票型のトゥートだったら投票する（期限切れでないかつ投票してないこと）
            if status['poll'] != None:
                if status['poll']['expired'] == False and not ('voted' in status['poll'] and status['poll']['voted'] == True):
                    voteOptions = status['poll']['options']
                    
                    # NGワードを検知した場合は弾いて好感度下げ
                    for voteSection in voteOptions:
                        if YuChan.ngWordHook(voteSection['title']):
                            log.logInfo('変なことを言ってはいけませんっ！！(*`ω´*): @{0}'.format(status['account']['acct']))
                            hooked = fav_rate.get(fav_rate.ID_Inst == user)
                            hooked.rate -= config['follow']['down_step']
                            hooked.save()
                            return
                    
                    # 設定で指定されたハッシュタグが含まれていない場合は投票をする
                    if not KotohiraUtil.isVoteOptout(status['tags']):
                        # ここで投票する場所を抽選
                        voteChoose = random.randint(0, len(voteOptions) - 1)
                        mastodon.poll_vote(status['poll']['id'], voteChoose)
                        # 投票したものをトゥートする
                        log.logInfo('投票っ！：@{0} => {1}'.format(status['account']['acct'], status['poll']['options'][voteChoose]['title']))
                        mastodon.status_post('ユウちゃんは「{0}」がいいと思いますっ！\n\n{1}'.format(status['poll']['options'][voteChoose]['title'], status['url']))
                        # 投票の再通知機能（設定で有効になっている場合のみ機能）
                        if config['features']['voteRenotify']:
                            # 投票締め切り時間を読み取って現在時刻からの差分でおおよその投票時間を逆算
                            expires_at = duParser.parse(status['poll']['expires_at'])
                            now_utc = utc.localize(now)
                            poll_time_delta = expires_at - now_utc
                            log.logInfo(poll_time_delta)
                            poll_time = poll_time_delta.seconds
                            # 約5分間投票だったら2分前ぐらいに通知、それ以外は5分前
                            if poll_time <= 310:
                                renotify_timer = float(120)
                            else:
                                renotify_timer = float(300)
                            log.logInfo(f'投票時間は{poll_time}ですので、{str(renotify_timer)}秒後に知らせますっ！')
                            VOTE_RENOTIFY_THREAD[int(status['id'])] = threading.Timer(renotify_timer, YuChan.vote_renotify, kwargs={
                                "url": status['url']
                            })
                            VOTE_RENOTIFY_THREAD[int(status['id'])].start()

            elif otherNick:
                # 他人のニックネームの設定
                YuChan.set_otherNickname(txt, status['id'], status['account']['id'], status['account']['acct'], status['visibility'])

            elif nick:
                # ニックネームの設定
                newNicknameParse = re.search(r"^(あだ名|あだな|ニックネーム)[:：は]\s?(.+)", txt)
                newNickname = newNicknameParse.group(2)
                YuChan.set_nickname(newNickname, status['id'], status['account']['id'], status['account']['acct'], status['visibility'])

            elif iBack:
                # おかえりとか言ったら実行
                if YuChan.msg_hook('wel_back', 600, ":@{0}: {1}、おかえりなさいませっ！".format(status['account']['acct'], name)):
                    log.logInfo('おかえりっ！：@{0} < {1}'.format(status['account']['acct'], txt))

            elif goodNight:
                # おやすみですっ！
                if YuChan.msg_hook('good_night', 600, ":@{0}: {1}、おやすみなさいっ！🌙".format(status['account']['acct'], name)):
                    log.logInfo('おやすみっ！:@{0} < {1}'.format(status['account']['acct'], txt))

            elif seeYou:
                # いってらっしゃいなのですっ！
                if YuChan.msg_hook('see_you', 600, ":@{0}: {1}、いってらっしゃいっ！🚪".format(status['account']['acct'], name)):
                    log.logInfo('いってらっしゃいっ！:@{0} < {1}'.format(status['account']['acct'], txt))                

            elif passage:
                # 通過 とか言ったら阻止しちゃうよっ！
                if YuChan.msg_hook('passage', 300, "阻止っ！！(*`ω´*)"):
                    log.logInfo('阻止っ！：@{0} < {1}'.format(status['account']['acct'], txt))

            elif sinkiSagi:
                # 現在時刻をUTCに変換し、該当アカウントの作成時刻から1日後のものを算出。
                # 作成から丸一日以上かつトゥートが10より上であれば作動
                now_utc = utc.localize(now)
                created_at = duParser.parse(status['account']['created_at'])
                created_a1d = created_at + datetime.timedelta(days=1)
                if status['account']['statuses_count'] > 10 and created_a1d < now_utc:
                    # 新規詐欺見破りっ！
                    if YuChan.msg_hook('sin_sagi', 600, "新規詐欺はいけませんっ！！(*`ω´*)"):
                        log.logInfo('新規詐欺っ！:@{0} < {1}'.format(status['account']['acct'], txt))
            
            elif nullPoint:
                # ぬるぽって、言ったら■━⊂( ･∀･)彡ｶﾞｯ☆`Дﾟ)
                if YuChan.msg_hook('null_point', 180, ":gaxtsu:"):
                    log.logInfo('がっ：@{0} < {1}'.format(status['account']['acct'], txt))

            elif notNicoFri:
                # ニコフレじゃないよっ！
                if YuChan.msg_hook('not_nikofure', 600, "ここはニコフレじゃないですっ！！ベスフレですっ！(*`ω´*)"):
                    log.logInfo('ベスフレですっ！：@{0} < {1}'.format(status['account']['acct'], txt))

            elif sad:
                # よしよしっ
                if YuChan.msg_hook('yoshiyoshi', 180, "(´･ω･`)ヾ(･ω･｡)ﾖｼﾖｼ"):
                    log.logInfo('よしよしっ：@{0} < {1}'.format(status['account']['acct'], txt))

            elif noNow:
                # いまのなしは封印ですっ！
                if YuChan.msg_hook('no_now', 180, "いまのなしは封印ですっ！！(*`ω´*)"):
                    log.logInfo('いまのなしは封印ですっ！：@{0} < {1}'.format(status['account']['acct'], txt))

            if writeDict:
                # 辞書登録っ
                # (実装中)
                # YuChan.update_userdict()
                pass
            
            elif writeMemo:
                # メモの書き込みっ
                memoBody = re.sub(r'^(メモ|めも|[Mm][Ee][Mm][Oo])[:：]\s*(.*)', r'\g<2>', txt, 1)
                mastodon.status_reblog(status['id'])
                log.logInfo('メモっ！：@{0} < {1}'.format(status['account']['acct'], txt))
                res = YuChan.write_memo(status['account']['acct'], memoBody, status['id'])
                if res == False:
                    mastodon.status_post('@{}\n長いのでまとめられそうにありませんっ・・・'.format(status['account']['acct']), in_reply_to_id=status['id'])

            # ２重更新防策
            if not newUser:
                updated_at = updated_users.get(updated_users.ID_Inst == user)
                greetableTime = updated_at.date + datetime.timedelta(hours=3)
                shouldGreet = now >= greetableTime
                # 3時間以上更新がなかった場合は挨拶する
                if shouldGreet:
                    time.sleep(0.5)
                    if now.hour < 12 and now.hour >= 5:
                        log.logInfo("おはようございますっ！：@{0} < {1}".format(status['account']['acct'], txt))
                        mastodon.toot(""":@{1}: {0}、おはようございますっ！🌄""".format(name, status['account']['acct']))
                    elif now.hour >= 12 and now.hour < 17:
                        log.logInfo("こんにちはっ！：@{0} < {1}".format(status['account']['acct'], txt))
                        mastodon.toot(""":@{1}: {0}、こんにちはっ！☀""".format(name, status['account']['acct']))
                    elif now.hour >= 17 and now.hour < 5:
                        log.logInfo("こんばんはっ！：@{0} < {1}".format(status['account']['acct'], txt))
                        mastodon.toot(""":@{1}: {0}、こんばんはっ！🌙""".format(name, status['account']['acct']))

                YuChan.drill_count(user, name, status['account']['statuses_count'])

                # 最終更新を変更
                updated_at.date = now
                updated_at.save()
    except Exception as e:
        DATABASE.rollback() # エラーが出た場合はデータベースのトランザクションを破棄
        # Timelines.pyの方へエラーを送出させる
        raise e
    else:
        DATABASE.commit() # 異常なければコミット

def local_onDelete(status_id):
    try:
        # メモのトゥートが削除されたらデータベースから削除する
        if YuChan.cancel_memo(status_id):
            log.logInfo(f"メモを削除っ！: {str(status_id)}")
        
        # 投票再通知の取り消し（該当する場合）
        if config['features']['voteRenotify'] and VOTE_RENOTIFY_THREAD.get(int(status_id), False):
            if type(VOTE_RENOTIFY_THREAD[int(status_id)]) == threading.Timer:
                VOTE_RENOTIFY_THREAD[int(status_id)].cancel()
                log.logInfo(f"投票再通知を解除っ！: {str(status_id)}")
    except Exception as e: # 上と同じ
        raise e
