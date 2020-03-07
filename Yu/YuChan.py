import datetime
import configparser
import random
import re
import json
import time
from pytz import timezone

from Yu.config import config
from Yu import log
from Yu.mastodon import mastodon
from Yu.database import DATABASE
from Yu.models import nickname, known_users, word_trigger, user_memos, fav_rate

# NGワードを予め読み込み（ファイルIOの負荷対策）
if config['features']['ngword']:
    with open('config/NGWORDS.txt', mode='r', encoding='utf-8_sig') as nfs:
        NGWORDS = []
        for ngw in nfs.readlines():
            # NGワードを追加。コメントを外す
            ngwWoC = re.sub('#.*', '', ngw).strip()
            # 変換後、空白でない場合は追加
            if ngwWoC != '':
                NGWORDS.append(ngwWoC)
else:
    NGWORDS = []

# フォロー解除例外ユーザーのプレリロード
EXCLUDEUSERSID = config['follow']['exclude']

def timeReport():
    now = datetime.datetime.now(timezone('Asia/Tokyo'))
    nowH = now.strftime("%H")
    if nowH == "12":
        mastodon.toot("琴平ユウちゃんが正午をお知らせしますっ！")
    elif nowH == "23":
        mastodon.toot("琴平ユウちゃんがテレホタイムをお知らせしますっ！")
    elif nowH == "00" or nowH == "0":
        mastodon.toot("琴平ユウちゃんが日付が変わったことをお知らせしますっ！")
    else:
        mastodon.toot(f"琴平ユウちゃんが{nowH}時をお知らせしますっ！")

def fortune(mentionId, acctId, visibility):
    # 乱数作成
    rnd = random.randrange(5)
    log.logInfo(f"占いっ！：@{acctId} => {rnd}")
    time.sleep(0.5)
    if rnd == 0:
        mastodon.status_post(f'@{acctId}\n🎉 大吉ですっ！', in_reply_to_id=mentionId, visibility=visibility)
    if rnd == 1:
        mastodon.status_post(f'@{acctId}\n👏 吉ですっ！', in_reply_to_id=mentionId, visibility=visibility)
    if rnd == 2:
        mastodon.status_post(f'@{acctId}\n👍 中吉ですっ！', in_reply_to_id=mentionId, visibility=visibility)
    if rnd == 3:
        mastodon.status_post(f'@{acctId}\n😞 末吉ですっ', in_reply_to_id=mentionId, visibility=visibility)
    if rnd == 4:
        mastodon.status_post(f'@{acctId}\n😥 凶ですっ・・・。', in_reply_to_id=mentionId, visibility=visibility)

def meow_time():
    mastodon.toot("にゃんにゃん！")

def rsp(txt, notification):
    # txtにHTMLタグ外しをしたテキスト、notificationに通知の生ファイルを入れる
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
        log.logInfo("じゃんけんっ！：@{0} => ✊ vs {1}".format(notification['account']['acct'], yuOttChooseEmoji))
        challengerChoose = "✊"
        if yuOttChoose == 0:
            isChallengerWin = None
        elif yuOttChoose == 1:
            isChallengerWin = True
        elif yuOttChoose == 2:
            isChallengerWin = False
    elif scissors:
        log.logInfo("じゃんけんっ！：@{0} => ✌ vs {1}".format(notification['account']['acct'], yuOttChooseEmoji))
        challengerChoose = "✌"
        if yuOttChoose == 0:
            isChallengerWin = False
        elif yuOttChoose == 1:
            isChallengerWin = None
        elif yuOttChoose == 2:
            isChallengerWin = True
    elif papers:
        log.logInfo("じゃんけんっ！：@{0} => ✋ vs {1}".format(notification['account']['acct'], yuOttChooseEmoji))
        challengerChoose = "✋"
        if yuOttChoose == 0:
            isChallengerWin = True
        elif yuOttChoose == 1:
            isChallengerWin = False
        elif yuOttChoose == 2:
            isChallengerWin = None

    time.sleep(0.5)
    if isChallengerWin == True:
        mastodon.status_post('@{0}\nあなた：{1}\nユウちゃん：{2}\n🎉 あなたの勝ちですっ！！'.format(notification['account']['acct'], challengerChoose, yuOttChooseEmoji), in_reply_to_id=notification['status']['id'], visibility=notification['status']['visibility'])
    elif isChallengerWin == None:
        mastodon.status_post('@{0}\nあなた：{1}\nユウちゃん：{2}\n👍 あいこですっ'.format(notification['account']['acct'], challengerChoose, yuOttChooseEmoji), in_reply_to_id=notification['status']['id'], visibility=notification['status']['visibility'])
    elif isChallengerWin == False:
        mastodon.status_post('@{0}\nあなた：{1}\nユウちゃん：{2}\n👏 ユウちゃんの勝ちですっ！'.format(notification['account']['acct'], challengerChoose, yuOttChooseEmoji), in_reply_to_id=notification['status']['id'], visibility=notification['status']['visibility'])

def set_nickname(name, reply_id, ID_Inst, acct, visibility):
    try:
        with DATABASE.transaction():
            # reply_idにリプライのIDをつける
            # 改行は削除
            name = name.replace('\n', '')
            # 32文字超えは弾きますっ！
            if len(name) > 32:
                log.logInfo('ニックネームが長いっ！：@{0} => {1}'.format(acct, name))
                mastodon.status_post(f'@{acct}\n長すぎて覚えられませんっ！！(*`ω´*)', in_reply_to_id=reply_id, visibility=visibility)
                return

            user = known_users.get(known_users.ID_Inst == ID_Inst)
            userNick = nickname.get_or_none(nickname.ID_Inst == user)

            if userNick == None:
                nickname.create(ID_Inst=user, nickname=name)
            else:
                userNick.nickname = name
                userNick.save()
            # 変更通知
            log.logInfo('ニックネーム変更っ！：@{0} => {1}'.format(acct, name))
            mastodon.status_post(f'@{acct}\nわかりましたっ！今度から\n「{name}」と呼びますねっ！', in_reply_to_id=reply_id, visibility=visibility)
    except Exception as e:
        DATABASE.rollback()
        raise e
    else:
        DATABASE.commit()

def show_nickname(reply_id, ID_Inst, acct, visibility):
    try:
        with DATABASE.transaction():
            user = known_users.get(known_users.ID_Inst == ID_Inst)
            showNickname = nickname.get_or_none(nickname.ID_Inst == user)
            if not showNickname == None:
                name = showNickname.nickname
                mastodon.status_post(f'@{acct}\nユウちゃんは「{name}」と呼んでいますっ！', in_reply_to_id=reply_id, visibility=visibility)
            else:
                mastodon.status_post(f'@{acct}\nまだあだ名はありませんっ！', in_reply_to_id=reply_id, visibility=visibility)            
    except Exception as e:
        DATABASE.rollback()
        raise e
    else:
        DATABASE.commit()

def del_nickname(reply_id, ID_Inst, acct, visibility):
    try:
        with DATABASE.transaction():
            user = known_users.get(known_users.ID_Inst == ID_Inst)
            delNickname = nickname.get_or_none(nickname.ID_Inst == user)
            if not delNickname == None:
                delNickname.delete_instance()
                log.logInfo('ニックネーム削除っ！：@{}'.format(acct))
                mastodon.status_post(f'@{acct}\nわかりましたっ！今度から普通に呼ばせていただきますっ！', in_reply_to_id=reply_id, visibility=visibility)
            else:
                log.logInfo('ニックネームを登録した覚えがないよぉ・・・：@{}'.format(acct))
                mastodon.status_post(f'@{acct}\nあれれ、ニックネームを登録した覚えがありませんっ・・・。', in_reply_to_id=reply_id, visibility=visibility)
    except Exception as e:
        DATABASE.rollback()
        raise e
    else:
        DATABASE.commit()

def set_otherNickname(txt, reply_id, fromID_Inst, fromAcct, visibility):
    try:
        with DATABASE.transaction():
            txtSearch = re.search(r"^(@[a-zA-Z0-9_]+\s|\n+)?:@([a-zA-Z0-9_]+):\sの(あだ名|あだな|ニックネーム)[:：は]\s?(.+)", txt)
            
            targetAcct = txtSearch.group(2)
            name = txtSearch.group(4)

            target = known_users.select().where(known_users.acct == targetAcct)

            # 変更先のニックネームと変更を指示したユーザーが同じ場合は、自分のニックネームを変更する関数へ引き渡し
            if target.ID_Inst == fromID_Inst:
                set_nickname(name, reply_id, fromID_Inst, fromAcct, visibility)
                return

            # ユーザーはユウちゃんにフォローされていることが前提条件
            Relation = mastodon.account_relationships(fromID_Inst)[0]
            if Relation['following'] == False:
                log.logInfo('フォローしていませんっ！：@{}'.format(fromAcct))
                mastodon.status_post(f'@{fromAcct}\n他の人の名前を変えるのはユウちゃんと仲良くなってからですっ！', in_reply_to_id=reply_id, visibility=visibility)
                return

            if target == 0:
                log.logInfo('知らないユーザーさんですっ・・・：@{}'.format(targetAcct))
                mastodon.status_post(f'@{fromAcct}\nユウちゃんその人知りませんっ・・・。', in_reply_to_id=reply_id, visibility=visibility)
                return
            else:
                targetID_Inst = target.ID_Inst
                targetUserInfo = nickname.select().where(nickname.ID_Inst == target)
                if targetUserInfo == 0:
                    nickname.create(ID_Inst=targetID_Inst, nickname=name)
                else:
                    updateNickname = nickname.get(nickname.ID_Inst == targetID_Inst)
                    updateNickname.nickname = name
                    updateNickname.create()

                log.logInfo('他人のニックネーム変更っ！：{0} => {1} : {2}'.format(fromAcct, targetAcct, name))
                mastodon.status_post(f':@{fromAcct}: @{fromAcct}\nわかりましたっ！ :@{targetAcct}: @{targetAcct} さんのことを今度から\n「{name}」と呼びますねっ！\n#ユウちゃんのあだ名変更日記')
                return True
    except Exception as e:
        DATABASE.rollback()
        raise e
    else:
        DATABASE.commit()

def msg_hook(triggerName, coolDown, sendFormat, status):
    try:
        with DATABASE.transaction():
            # タイムラインで正規表現にかかった場合に実行
            # status(生の情報)とKotohiraMemoryクラス情報を受け流す必要がある
            now = datetime.datetime.now()
            
            trigger = word_trigger.get_or_none(word_trigger.trigger_name == triggerName)
            if trigger == None:
                trigger = word_trigger.create(trigger_name=triggerName)
                doIt = True
            else:
                # 前回の実行から指定秒数までクールダウンしたかを確認して実行するか決める
                if now >= (trigger.date + datetime.timedelta(seconds=coolDown)):
                    doIt = True
                else:
                    doIt = False

            # 実行可能な状態であれば実行
            if doIt:
                time.sleep(0.5)
                mastodon.toot(sendFormat)
                trigger.date = now
                trigger.save()
            
            return doIt
    except Exception as e:
        DATABASE.rollback()
        raise e
    else:
        DATABASE.commit()

def write_memo(fromUser, body, statusId):
    try:
        with DATABASE.transaction():
            # メモを書き込むっ！50文字以内であることが条件っ！
            body.strip()
            if len(body) > 50:
                # 50文字オーバーの場合は弾く
                return False
            now = datetime.datetime.now(timezone('Asia/Tokyo'))
            # 55分以降の場合は現在時刻から6分送り、次の時間へ持ち越せるようにする
            if now.minute >= 55:
                now += datetime.timedelta(minutes=6)
            
            memoTime = now.strftime("%Y_%m%d_%H%z")
            memo, _ = user_memos.get_or_create(memo_time=memoTime)
            memRaw = json.loads(memo.body)
            memRaw.append({'from': fromUser, 'body': body, 'id': int(statusId)})
            memo.body = json.dumps(memRaw, ensure_ascii=False)
            memo.save()
    except Exception as e:
        DATABASE.rollback()
        raise e
    else:
        DATABASE.commit()

def toot_memo():
    try:
        with DATABASE.transaction():
            # その時間帯に集められたメモを集約して投稿っ！
            now = datetime.datetime.now(timezone('Asia/Tokyo'))
            memo = user_memos.get_or_none(user_memos.memo_time == now.strftime("%Y_%m%d_%H%z"))
            # データがない場合は何もしない
            if memo != None:
                memRaw = json.loads(memo.body)
                if len(memRaw) == 0:
                    # JSONが空だったらトゥート中止
                    return
                # for文に入るための変数初期化
                tootList = []
                tootSep = 0
                tootBody = ['']
                # 一度トゥート文型化してリストに挿入
                for i in memRaw:
                    tootList.append( ":@{0}: {1}\n".format(i['from'], i['body']))
                # トゥート可能な文面にする
                for i, body in enumerate(tootList):
                    # 内容が5件超える場合はセパレート（enumerateで0の場合は例外）
                    if not i == 0 and i % 5 == 0:
                        tootBody.append('')
                        tootSep += 1
                    tootBody[tootSep] += body
                # まとめる
                sepCount = 0
                for t in tootBody:
                    tootCwTemplate = "{0}時のメモのまとめですっ！({1}/{2})".format(now.hour, sepCount + 1, tootSep + 1)
                    mastodon.status_post(t + "\n#ユウちゃんのまとめメモ", spoiler_text=tootCwTemplate)
                    sepCount += 1
    except Exception as e:
        DATABASE.rollback()
        raise e
    else:
        DATABASE.commit()

def cancel_memo(status_id):
    try:
        with DATABASE.transaction():
            # トゥートが削除された時に実行
            now = datetime.datetime.now(timezone('Asia/Tokyo'))
            if now.minute >= 55:
                now += datetime.timedelta(minutes=6)
            memo = user_memos.get_or_none(user_memos.memo_time == now.strftime("%Y_%m%d_%H%z"))
            # メモがその時間にない場合は無視
            if memo == None:
                return False
            
            commitable = False

            memRaw = json.loads(memo.body)
            for memoStat in memRaw:
                if int(status_id) == memoStat.get('id'):
                    # IDが合致した場合は削除し、コミットするようにする
                    # IDは重複することはないので、一度合致したらfor文を抜ける
                    memRaw.remove(memoStat)
                    commitable = True
                    break

            if commitable:
                # for文で回して差分がある場合はコミットしてTrueを返す
                memo.body = json.dumps(memRaw, ensure_ascii=False)
                memo.save()
                return True
            else:
                # 差分がない場合はFalse
                return False
    except Exception as e:
        DATABASE.rollback()
        raise e
    else:
        DATABASE.commit()

# 実装中

def userdict(targetUser, fromUser, body, replyTootID):
    pass

# NGワード検出機能
def ngWordHook(txt):
    # 設定で無効化されている場合はFalseを返す
    if config['features']['ngword']:
        # 予め読み込んだNGワードリストを使用
        for ngword in NGWORDS:
            # 正規表現も使えるようにしている
            if re.search(ngword, txt):
                # 見つかった場合はTrueを返す
                return True
        # for文回しきって見つからなかった場合はFalseを返す
        return False
    else:
        return False

# 一定の好感度レートが下がってしまうとフォローが外れちゃいますっ・・・。
def unfollow_attempt(targetID_Inst):
    # ただし、設定で入力したユーザーIDはフォローを外しませんっ！
    if targetID_Inst in EXCLUDEUSERSID:
        return
    try:
        with DATABASE.transaction():
            user = known_users.get(known_users.ID_Inst == targetID_Inst)
            target = fav_rate.get(fav_rate.ID_Inst == user)
            relation = mastodon.account_relationships(targetID_Inst)[0]
            if relation['following'] == True and int(target.rate) < int(config['follow']['condition_rate']):
                log.logInfo('ゴメンねっ・・・。: {}'.format(str(targetID_Inst)))
                mastodon.account_unfollow(targetID_Inst)
    except Exception as e:
        DATABASE.rollback()
        raise e
    else:
        DATABASE.commit()

def drill_count(targetID, name, statCount):
    if statCount <= 10000: # トゥート数が10,000以下の場合は1,000トゥート単位で処理しますっ！
        if statCount % 1000 == 0:
            tootable =  True
        else:
            tootable = False
    else:
        if statCount % 10000 == 0:
            tootable = True
        else:
            tootable = False

    if tootable:
        mastodon.toot(f"@{targetID}\n:@{targetID}: {name}、{statCount:,}トゥート達成おめでとうございますっ！🎉")

# あなたとユウちゃんのこと教えますっ！
def about_you(targetID_Inst, mentionId, visibility):
    try:
        with DATABASE.transaction():
            target = known_users.get(known_users.ID_Inst == targetID_Inst)
            known_at_str = target.known_at.strftime("%Y月%m月%d日 %H:%M:%S")

            mastodon.status_post(f'@{target.acct}\n ユウちゃんは{known_at_str}にあなたのことを覚えて、{target.ID}番目に知りましたっ！', in_reply_to_id=mentionId, visibility=visibility)
    except Exception as e:
        DATABASE.rollback()
        raise e
    else:
        DATABASE.commit()
