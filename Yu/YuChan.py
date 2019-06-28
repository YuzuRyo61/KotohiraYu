# -*- coding: utf-8 -*-

import datetime
import configparser
import random
import re
import json
import time
from pytz import timezone
from mastodon import Mastodon

from Yu.Memory import KotohiraMemory
from Yu.Timer import Timer

config = configparser.ConfigParser()
config.read('config/config.ini')

mastodon = Mastodon(
    access_token='config/accesstoken.txt',
    api_base_url=config['instance']['address']
)

# NGワードを予め読み込み（ファイルIOの負荷対策）
NGWORDS = []

with open('config/NGWORDS.txt', 'r') as nfs:
    for ngw in nfs.readlines():
        # NGワードを追加。コメントを外す
        ngwWoC = re.sub('#.*', '', ngw).strip()
        # 変換後、空白でない場合は追加
        if ngwWoC != '':
            NGWORDS.append(ngwWoC)

class YuChan:
    @staticmethod
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

    @staticmethod
    def fortune(mentionId, acctId, visibility):
        # 乱数作成
        rnd = random.randrange(5)
        print(f"占いっ！：@{acctId} => {rnd}")
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
    
    @staticmethod
    def meow_time():
        mastodon.toot("にゃんにゃん！")

    @staticmethod
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

        time.sleep(0.5)
        if isChallengerWin == True:
            mastodon.status_post('@{0}\nあなた：{1}\nユウちゃん：{2}\n🎉 あなたの勝ちですっ！！'.format(notification['account']['acct'], challengerChoose, yuOttChooseEmoji), in_reply_to_id=notification['status']['id'], visibility=notification['status']['visibility'])
        elif isChallengerWin == None:
            mastodon.status_post('@{0}\nあなた：{1}\nユウちゃん：{2}\n👍 あいこですっ'.format(notification['account']['acct'], challengerChoose, yuOttChooseEmoji), in_reply_to_id=notification['status']['id'], visibility=notification['status']['visibility'])
        elif isChallengerWin == False:
            mastodon.status_post('@{0}\nあなた：{1}\nユウちゃん：{2}\n👏 ユウちゃんの勝ちですっ！'.format(notification['account']['acct'], challengerChoose, yuOttChooseEmoji), in_reply_to_id=notification['status']['id'], visibility=notification['status']['visibility'])

    @staticmethod
    def set_nickname(txt, reply_id, ID_Inst, acct, visibility, ktMemory):
        # txtはHTMLタグ除去を施したもの、reply_idにリプライのIDをつける
        userInfo = ktMemory.select('nickname', ID_Inst)
        # 定義プレフィックス削除
        name = re.sub(r'^(@[a-zA-Z0-9_]+(\s|\n)?)?(あだ(名|な)|ニックネーム)[:：は]\s?', '', txt, 1)
        # @(半角)を含むもの、コロンは除去
        name = re.sub(r'[：:@]+', '', name)
        # 改行は削除
        name = name.replace('\n', '')
        # 30文字超えは弾きますっ！
        if len(name) > 30:
            print('ニックネームが長いっ！：@{0} => {1}'.format(acct, name))
            mastodon.status_post(f'@{acct}\n長すぎて覚えられませんっ！！(*`ω´*)', in_reply_to_id=reply_id, visibility=visibility)
            return
        if len(userInfo) == 0:
            ktMemory.insert('nickname', ID_Inst, name)
        else:
            ktMemory.update('nickname', name, ID_Inst)
        # 変更通知
        print('ニックネーム変更っ！：@{0} => {1}'.format(acct, name))
        mastodon.status_post(f'@{acct}\nわかりましたっ！今度から\n「{name}」と呼びますねっ！', in_reply_to_id=reply_id, visibility=visibility)
    
    @staticmethod
    def del_nickname(reply_id, ID_Inst, acct, visibility, ktMemory):
        isexistname = ktMemory.select('nickname', ID_Inst)
        if len(isexistname) != 0:
            ktMemory.delete('nickname', ID_Inst)
            print('ニックネーム削除っ！：@{}'.format(acct))
            mastodon.status_post(f'@{acct}\nわかりましたっ！今度から普通に呼ばせていただきますっ！', in_reply_to_id=reply_id, visibility=visibility)
        else:
            print('ニックネームを登録した覚えがないよぉ・・・：@{}'.format(acct))
            mastodon.status_post(f'@{acct}\nあれれ、ニックネームを登録した覚えがありませんっ・・・。', in_reply_to_id=reply_id, visibility=visibility)

    @staticmethod
    def msg_hook(tableName, coolDown, sendFormat, status, ktMemory):
        # タイムラインで正規表現にかかった場合に実行
        # status(生の情報)とKotohiraMemoryクラス情報を受け流す必要がある
        userInfo = ktMemory.select(tableName, status['account']['id'])
        now = datetime.datetime.now(timezone('Asia/Tokyo'))
        dt = now.strftime("%Y-%m-%d %H:%M:%S%z")
        if len(userInfo) == 0:
            # データがない場合はデータ挿入して実行
            ktMemory.insert(tableName, status['account']['id'], dt)
            doIt = True
        else:
            didWBAt = userInfo[0][2]
            didWBAtRaw = datetime.datetime.strptime(didWBAt, '%Y-%m-%d %H:%M:%S%z')
            dateDiff = now >= (didWBAtRaw + datetime.timedelta(seconds=coolDown))

            # 前回の実行から指定秒数までクールダウンしたかを確認して実行するか決める
            if dateDiff == True:
                doIt = True
            else:
                doIt = False

        globalDate = ktMemory.select('latest_ran', tableName)
        # 現在時刻から1分先がグローバルクールダウンタイム
        globalDeltaRaw = now + datetime.timedelta(minutes=1)
        globalDelta = globalDeltaRaw.strftime("%Y-%m-%d %H:%M:%S%z")
        if len(globalDate) == 0:
            # テーブル名が見つからなかった場合は挿入して実行
            ktMemory.insert('latest_ran', tableName, globalDelta)
            globalCoolDowned = True
        else:
            # 差異を検証する
            globalCooldownRaw = datetime.datetime.strptime(globalDate[0][2], "%Y-%m-%d %H:%M:%S%z")
            globalCooldownDiff = now >= globalCooldownRaw
            if globalCooldownDiff: # 60秒以上であればグローバルクールダウン済み
                globalCoolDowned = True
            else:
                globalCoolDowned = False

        # 実行可能な状態であるかつ、グローバルクールダウンが終わったかを確認し、実行
        if doIt and globalCoolDowned == True:
            time.sleep(0.5)
            mastodon.toot(sendFormat)
            ktMemory.update(tableName, dt, status['account']['id'])
            ktMemory.update('latest_ran', globalDelta, tableName)
        
        return doIt

    @staticmethod
    def write_memo(fromUser, body, ktMemory):
        # メモを書き込むっ！30文字以内であることが条件っ！
        if len(body) > 30:
            # 30文字オーバーの場合は弾く
            return False
        now = datetime.datetime.now(timezone('Asia/Tokyo'))
        # 55分以降の場合は現在時刻から6分送り、次の時間へ持ち越せるようにする
        if len(now.minute) >= 55:
            now += datetime.timedelta(minutes=6)
        dt = now.strftime("%Y_%m%d_%H%z")
        memo = ktMemory.select('user_memos', dt)
        if len(memo) == 0:
            # データがない場合は新しく挿入
            memRaw = [{'from': fromUser, 'body': body}]
            memJson = json.dumps(memRaw)
            ktMemory.insert('user_memos', dt, memJson)
        else:
            # データがある場合は読み込んで更新
            memJson = memo[0][2]
            memRaw = json.loads(memJson)
            memRaw.append({'from': fromUser, 'body': body})
            memNewJson = json.dumps(memRaw)
            ktMemory.update('user_memos', memNewJson, dt)

    @staticmethod
    def toot_memo():
        # その時間帯に集められたメモを集約して投稿っ！
        memory = KotohiraMemory(showLog=config['log'].getboolean('enable'))
        now = datetime.datetime.now(timezone('Asia/Tokyo'))
        dt = now.strftime("%Y_%m%d_%H%z")
        memo = memory.select('user_memos', dt)
        # データがない場合は何もしない
        if len(memo) != 0:
            memRaw = json.loads(memo[0][2])
            # for文に入るための変数初期化
            tootList = []
            tootSep = 0
            tootBody = ['']
            # 一度トゥート文型化してリストに挿入
            for i in memRaw:
                tootList.append( ":@{0}: {1}\n".format(i['from'], i['body']))
            # トゥート可能な文面にする
            for i in tootList:
                # 内容の文字数が450を超える場合はセパレート
                if (len(tootBody[tootSep])) > 450:
                    tootBody.append('')
                    tootSep += 1
                tootBody[tootSep] += i
            # まとめる
            sepCount = 0
            for t in tootBody:
                tootCwTemplate = "{0}時のメモのまとめですっ！({1}/{2})".format(now.hour, sepCount + 1, tootSep + 1)
                mastodon.status_post(t, spoiler_text=tootCwTemplate)
        
        # クリーンアップ
        del memory

    # 実装中
    @staticmethod
    def userdict(targetUser, fromUser, body, replyTootID, ktMemory):
        pass

    # NGワード検出機能
    @staticmethod
    def ngWordHook(txt):
        # 予め読み込んだNGワードリストを使用
        for ngword in NGWORDS:
            # 正規表現も使えるようにしている
            if re.search(ngword, txt):
                # 見つかった場合はTrueを返す
                return True
        # for文回しきって見つからなかった場合はFalseを返す
        return False
