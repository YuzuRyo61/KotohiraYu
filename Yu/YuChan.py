# -*- coding: utf-8 -*-

import datetime
import configparser
import random
import re
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

class YuChan:
    @staticmethod
    def timeReport():
        now = datetime.datetime.now(timezone('Asia/Tokyo'))
        nowH = now.strftime("%H")
        if nowH == "12":
            mastodon.toot(f"琴平ユウちゃんが正午をお知らせしますっ！")
        elif nowH == "23":
            mastodon.toot(f"琴平ユウちゃんがテレホタイムをお知らせしますっ！")
        elif nowH == "00" or nowH == "0":
            mastodon.toot(f"琴平ユウちゃんが日付が変わったことをお知らせしますっ！")
        else:
            mastodon.toot(f"琴平ユウちゃんが{nowH}時をお知らせしますっ！")

    @staticmethod
    def fortune(mentionId, acctId):
        # 乱数作成
        rnd = random.randrange(5)
        print(f"占いっ！：@{acctId} => {rnd}")
        if rnd == 0:
            mastodon.status_post(f'@{acctId}\n🎉 大吉ですっ！', in_reply_to_id=mentionId)
        if rnd == 1:
            mastodon.status_post(f'@{acctId}\n👏 吉ですっ！', in_reply_to_id=mentionId)
        if rnd == 2:
            mastodon.status_post(f'@{acctId}\n👍 中吉ですっ！', in_reply_to_id=mentionId)
        if rnd == 3:
            mastodon.status_post(f'@{acctId}\n😞 末吉ですっ', in_reply_to_id=mentionId)
        if rnd == 4:
            mastodon.status_post(f'@{acctId}\n😥 凶ですっ・・・。', in_reply_to_id=mentionId)
    
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

        if isChallengerWin == True:
            mastodon.status_post('@{0}\nあなた：{1}\nユウちゃん：{2}\n🎉 あなたの勝ちですっ！！'.format(notification['account']['acct'], challengerChoose, yuOttChooseEmoji), in_reply_to_id=notification['status']['id'])
        elif isChallengerWin == None:
            mastodon.status_post('@{0}\nあなた：{1}\nユウちゃん：{2}\n👍 あいこですっ'.format(notification['account']['acct'], challengerChoose, yuOttChooseEmoji), in_reply_to_id=notification['status']['id'])
        elif isChallengerWin == False:
            mastodon.status_post('@{0}\nあなた：{1}\nユウちゃん：{2}\n👏 ユウちゃんの勝ちですっ！'.format(notification['account']['acct'], challengerChoose, yuOttChooseEmoji), in_reply_to_id=notification['status']['id'])

    @staticmethod
    def set_nickname(txt, reply_id, ID_Inst, acct, ktMemory):
        # txtはHTMLタグ除去を施したもの、reply_idにリプライのIDをつける
        userInfo = ktMemory.select('nickname', ID_Inst)
        name = re.sub(r'^(@[a-zA-Z0-9_]+(\s|\n)?)?(あだ(名|な)|ニックネーム)[:：は]?\s?', '', txt, 1)
        name = name.replace('\n', '')
        if len(userInfo) == 0:
            ktMemory.insert('nickname', ID_Inst, name)
        else:
            ktMemory.update('nickname', name, ID_Inst)
        # 変更通知
        print('ニックネーム変更っ！：@{0} => {1}'.format(acct, name))
        mastodon.status_post(f'@{acct}\nわかりましたっ！今度から\n「{name}」と呼びますねっ！', in_reply_to_id=reply_id)
    
    @staticmethod
    def del_nickname(reply_id, ID_Inst, acct, ktMemory):
        isexistname = ktMemory.select('nickname', ID_Inst)
        if len(isexistname) != 0:
            ktMemory.delete('nickname', ID_Inst)
            print('ニックネーム削除っ！：@{}'.format(acct))
            mastodon.status_post(f'@{acct}\nわかりましたっ！今度から普通に呼ばせていただきますっ！', in_reply_to_id=reply_id)
        else:
            print('ニックネームを登録した覚えがないよぉ・・・：@{}'.format(acct))
            mastodon.status_post(f'@{acct}\nあれれ、ニックネームを登録した覚えがありませんっ・・・。', in_reply_to_id=reply_id)

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

        # グローバルクールダウンしたを確認する
        if doIt and globalCoolDowned == True:
            mastodon.toot(sendFormat)
            ktMemory.update(tableName, dt, status['account']['id'])
            ktMemory.update('latest_ran', globalDelta, tableName)
        
        return doIt
