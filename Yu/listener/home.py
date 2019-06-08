# -*- coding: utf-8 -*-
import configparser
import re

from mastodon import Mastodon, StreamListener

from Yu import KotohiraMemory, KotohiraUtil, YuChan

config = configparser.ConfigParser()
config.read('config/config.ini')

mastodon = Mastodon(
    access_token='config/accesstoken.txt',
    api_base_url=config['instance']['address']
)

# ホームタイムラインのリスナー(主に通知リスナー)
class user_listener(StreamListener):
    def on_notification(self, notification):
        # bot属性のアカウントの場合は無視する
        if notification['account']['bot'] == True:
            return
        # 代入してちょっと見栄え良く
        notifyType = notification['type']
        if notifyType == 'mention':
            # 返信とか

            # テキスト化
            txt = KotohiraUtil.h2t(notification['status']['content'])

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
