import configparser
import re
import time

from mastodon import StreamListener

from Yu import YuChan, log, Util as KotohiraUtil
from Yu.config import config
from Yu.mastodon import mastodon
from Yu.database import DATABASE
from Yu.models import fav_rate, known_users, recent_fav

# ホームタイムラインのリスナー(主に通知リスナー)
class user_listener(StreamListener):
    def on_update(self, status):
        try:
            with DATABASE.transaction():
                # 公開範囲が「公開」であればここのリスナーでは無視する
                if status['visibility'] == 'public':
                    return
                
                # 連合アカウントである場合(@が含まれている)は無視する
                if status['account']['acct'].find('@') != -1:
                    return

                # Botアカウントは応答しないようにする
                if status['account']['bot'] == True:
                    return

                # 自分のトゥートは無視
                if config['user']['me'] == status['account']['acct']:
                    return

                # トゥート内のHTMLタグを除去
                txt = KotohiraUtil.h2t(status['content'])

                # 自分宛てのメンションはここのリスナーでは無視する（ユーザー絵文字の場合は例外）
                isMeMention = re.search('(?!.*:)@({}+)(?!.*:)'.format(config['user']['me']), txt)
                if isMeMention:
                    return

                calledYuChan = re.search(f'(琴平|ことひら|コトヒラ|ｺﾄﾋﾗ|:@{config["user"]["me"]}:|((ゆう|ユウ|ユゥ|ﾕｳ|ﾕｩ)(ちゃん|チャン|ﾁｬﾝ|くん|クン|君|ｸﾝ))|ユウ)', txt)

                # ユウちゃん etc... とか呼ばれたらふぁぼる
                if calledYuChan:
                    log.logInfo('呼ばれたっ！：@{0} < {1}'.format(status['account']['acct'], txt))
                    if not status['favourited']:
                        mastodon.status_favourite(status['id'])
                        # 好感度ちょいアップ
                        calledBy = known_users.get(known_users.ID_Inst == status['account']['id'])
                        calledByRate = fav_rate.get(fav_rate.ID_Inst == calledBy)
                        calledByRate += 1
                        calledByRate.save()
                    else:
                        log.logWarn('ふぁぼってましたっ！')

        except Exception as e:
            DATABASE.rollback()
            # Timelines.pyの方へエラーを送出させる
            raise e
        else:
            DATABASE.commit()

    def on_notification(self, notification):
        try:
            with DATABASE.transaction():
                # bot属性のアカウントの場合は無視する
                if notification['account']['bot'] == True:
                    return

                # 連合アカウントである場合(@が含まれている)は無視する
                if notification['account']['acct'].find('@') != -1:
                    return

                # 代入してちょっと見栄え良く
                notifyType = notification['type']
                if notifyType == 'mention':
                    # 知っているユーザーであるか
                    # 知らないユーザーの場合はここで弾く
                    user = known_users.get_or_none(known_users.ID_Inst == notification['account']['id'])
                    if user == None:
                        return

                    # テキスト化
                    txt = KotohiraUtil.h2t(notification['status']['content'])

                    # 口頭のメンションを除去
                    txt = re.sub(r'^(@[a-zA-Z0-9_]+)?(\s|\n)*', '', txt)

                    # とりあえずふぁぼる
                    log.logInfo('お手紙っ！：@{0} < {1}'.format(notification['account']['acct'], txt))
                    mastodon.status_favourite(notification['status']['id'])

                    # NGワードを検知した場合は弾いて好感度下げ
                    if YuChan.ngWordHook(txt):
                        log.logInfo('変なことを言ってはいけませんっ！！(*`ω´*): @{0}'.format(notification['account']['acct']))
                        hooked = fav_rate.get(fav_rate.ID_Inst == user)
                        hooked.rate -= config['follow']['down_step']
                        hooked.save()
                        time.sleep(0.5)
                        mastodon.status_post('@{}\n変なこと言っちゃいけませんっ！！(*`ω´*)'.format(notification['account']['acct']), in_reply_to_id=notification['status']['id'], visibility=notification['status']['visibility'])
                        YuChan.unfollow_attempt(notification['account']['id'])
                        return

                    # 好感度を少し上げる
                    notifyBy = fav_rate.get(fav_rate.ID_Inst == user)
                    notifyBy.rate += 1
                    notifyBy.save()

                    # 正規表現とか
                    followReq = re.search(r'(フォロー|[Ff]ollow|ふぉろー)(して|.?頼(む|みたい|もう)|.?たの(む|みたい|もう)|お願い|おねがい)?', txt)
                    fortune = re.search(r'(占|うらな)(って|い)', txt)
                    showNick = re.search(r'(ぼく|ボク|僕|わたし|ワタシ|私|俺|おれ|オレ|うち|わし|あたし|あたい)の(ニックネーム|あだな|あだ名|名前|なまえ)', txt)
                    deleteNick = re.search(r'^(ニックネーム|あだ名)を?(消して|削除|けして|さくじょ)', txt)
                    otherNick = re.search(r'^:@([a-zA-Z0-9_]+):\sの(あだ名|あだな|ニックネーム)[:：は]\s?(.+)', txt)
                    nick = re.search(r'^(@[a-zA-Z0-9_]+(\s|\n)+)?(あだ名|あだな|ニックネーム)[:：は]\s?(.+)', txt)
                    rspOtt = re.search(r'じゃんけん\s?(グー|✊|👊|チョキ|✌|パー|✋)', txt)
                    isPing = re.search(r'[pP][iI][nN][gG]', txt)
                    love = re.search(r'(すき|好き|しゅき|ちゅき)', txt)
                    aboutYou = re.search(r'(ぼく|ボク|僕|わたし|ワタシ|私|俺|おれ|オレ|うち|わし|あたし|あたい)の(事|こと)', txt)

                    # メンションでフォローリクエストされたとき
                    if followReq:
                        reqRela = mastodon.account_relationships(notification['account']['id'])[0]
                        # フォローしていないこと
                        if reqRela['following'] == False:
                            if reqRela['followed_by'] == True: # フォローされていること
                                if int(notifyBy.rate) >= int(config['follow']['condition_rate']): # 設定で決めた好感度レート以上だったら合格
                                    log.logInfo('フォローっ！：@{}'.format(notification['account']['acct']))
                                    mastodon.account_follow(notification['account']['id'])
                                    mastodon.status_post('@{}\nフォローしましたっ！これからもよろしくねっ！'.format(notification['account']['acct']), in_reply_to_id=notification['status']['id'], visibility=notification['status']['visibility'])
                                else: # 不合格の場合はレスポンスして終了
                                    log.logInfo('もうちょっと仲良くなってからっ！：@{}'.format(notification['account']['acct']))
                                    mastodon.status_post('@{}\nもうちょっと仲良くなってからですっ！'.format(notification['account']['acct']), in_reply_to_id=notification['status']['id'], visibility=notification['status']['visibility'])
                            else:
                                log.logInfo('先にフォローしてっ！:@{}'.format(notification['account']['acct']))
                                mastodon.status_post('@{}\nユウちゃんをフォローしてくれたら考えますっ！'.format(notification['account']['acct']), in_reply_to_id=notification['status']['id'], visibility=notification['status']['visibility'])
                        else: # フォローしている場合は省く
                            log.logInfo('フォロー済みっ！：@{}'.format(notification['account']['acct']))
                            mastodon.status_post('@{}\nもうフォローしてますっ！'.format(notification['account']['acct']), in_reply_to_id=notification['status']['id'], visibility=notification['status']['visibility'])
                    
                    # 占いのリクエストがされたとき
                    elif fortune:
                        YuChan.fortune(notification['status']['id'], notification['account']['acct'], notification['status']['visibility'])
                        # 更に４つ加算
                        notifyBy.rate += 4
                        notifyBy.save()

                    # ニックネームの照会
                    elif showNick:
                        YuChan.show_nickname(notification['status']['id'], notification['account']['id'], notification['account']['acct'], notification['status']['visibility'])

                    # ニックネームの削除
                    elif deleteNick:
                        YuChan.del_nickname(notification['status']['id'], notification['account']['id'], notification['account']['acct'], notification['status']['visibility'])

                    # 他人のニックネームの設定
                    elif otherNick:
                        YuChan.set_otherNickname(txt, notification['status']['id'], notification['account']['id'], notification['account']['acct'], notification['status']['visibility'])

                    # ニックネームの設定
                    elif nick:
                        newNicknameParse = re.search(r"^(@[a-zA-Z0-9_]+(\s|\n)+)?(あだ名|あだな|ニックネーム)[:：は]\s?(.+)", txt)
                        newNickname = newNicknameParse.group(4)
                        YuChan.set_nickname(newNickname, notification['status']['id'], notification['account']['id'], notification['account']['acct'], notification['status']['visibility'])

                    # ユウちゃんとじゃんけんっ！
                    elif rspOtt:
                        YuChan.rsp(txt, notification)
                        # 更に４つ加算
                        notifyBy.rate += 4
                        notifyBy.save()

                    # 応答チェッカー
                    elif isPing:
                        log.logInfo('PINGっ！：@{}'.format(notification['account']['acct']))
                        mastodon.status_post('@{}\nPONG!'.format(notification['account']['acct']), in_reply_to_id=notification['status']['id'], visibility=notification['status']['visibility'])

                    elif love:
                        if int(notifyBy.rate) >= int(config['follow']['condition_rate']):
                            log.logInfo('❤：@{}'.format(notification['account']['acct']))
                            mastodon.status_post('@{}\nユウちゃんも好きですっ！❤'.format(notification['account']['acct']), in_reply_to_id=notification['status']['id'], visibility=notification['status']['visibility'])
                        elif int(notifyBy.rate) < 0:
                            log.logInfo('...: @{}'.format(notification['account']['acct']))
                        else:
                            log.logInfo('//：@{}'.format(notification['account']['acct']))
                            mastodon.status_post('@{}\nは、恥ずかしいですっ・・・//'.format(notification['account']['acct']), in_reply_to_id=notification['status']['id'], visibility=notification['status']['visibility'])

                    elif aboutYou:
                        log.logInfo("@{}の事、教えますっ！".format(notification['account']['acct']))
                        YuChan.about_you(notification['account']['id'], notification['status']['id'], notification['status']['visibility'])
                
                elif notifyType == 'favourite':
                    # ふぁぼられ
                    log.logInfo('ふぁぼられたっ！：@{0}'.format(notification['account']['acct']))
                    # ふぁぼ連対策
                    user = known_users.get(known_users.ID_Inst == notification['account']['id'])
                    userRate = fav_rate.get(fav_rate.ID_Inst == user)
                    favInfo, created = recent_fav.get_or_create(ID_Inst=user)
                    if created:
                        # データが作成された場合は好感度アップ
                        favInfo.tootID = notification['status']['id']
                        favInfo.save()
                        userRate.rate += 1
                        userRate.save()
                    else:
                        # 最後にふぁぼったトゥートが同じものでないこと
                        if notification['status']['id'] != favInfo.tootID:
                            favInfo.tootID = notification['status']['id']
                            favInfo.save()
                            userRate.rate += 1
                            userRate.save()

                
                elif notifyType == 'reblog':
                    # ブーストされ
                    log.logInfo('ブーストされたっ！：@{0}'.format(notification['account']['acct']))
                    # ふぁぼられと同様な機能とか
                
                elif notifyType == 'follow':
                    # フォローされ
                    log.logInfo('フォローされたっ！：@{0}'.format(notification['account']['acct']))
        except Exception as e:
            DATABASE.rollback()
            # Timelines.pyの方へエラーを送出させる
            raise e
        else:
            DATABASE.commit()
