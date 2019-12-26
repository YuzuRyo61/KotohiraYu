# Kotohira Yu

YuzuRyo61 Presents

The mastodon bot!

琴平ユウ（愛称名：ユウちゃん）のソースコードです。

[プロフィールを見たい人はこちら。](PROFILE.md)

## Getting started

※pipenvをインストールしていない場合は最初にインストールしてください：```pip install pipenv```

1. pipenvの環境を作ります

   ```pipenv --python 3```

2. 必要パッケージをインストールします

   ```pipenv install```

3. config.tomlを設定する

4. accesstoken.txtにアクセストークンを入れる

5. KotohiraYu.pyを実行する

これだけですっ！

※systemdに登録しておくと便利です

## こちらで運用しています（本家アカウント）

[@Yu@best-friends.chat](https://best-friends.chat/@Yu)

## 注意事項など

- Python 3以降で動作します。Python 2は動作保証外です。

- Linuxでの動作を想定した設計になっているため、その他のOSでは上手く動作しない可能性がありますのでご注意ください。

- ユーザーのアカウント画像の絵文字が使用できるインスタンスを使用しています。そのため、その機能がついていないインスタンスの場合はお手数ですが適宜調節をお願いいたします。

- 連合アカウントには対応していません。ローカルオンリーです。連合に対応させると色々と面倒なので。

- 機能の要望やバグ修正などはMastodonなどのActivityPub対応システムで、ハッシュタグ #YuChanIssues にて受け付けております。
  もしくはIssuesかメンション([@YuzuRyo61@best-friends.chat](https://best-friends.chat/@YuzuRyo61))でどうぞ。

- *ユウちゃんをうちの子にしたかったらフォークしてくれ。*

## License

MIT License. See [LICENSE](LICENSE)

## Special Thanks

Social preview(and official production account header image): [@elfin@best-friends.chat](https://best-friends.chat/@elfin)
