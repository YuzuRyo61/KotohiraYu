# Kotohira Yu

YuzuRyo61 Presents

The mastodon bot!

琴平ユウ（愛称名：ユウちゃん）のソースコードです。

[プロフィールを見たい人はこちら。](PROFILE.md)

## Getting started

**※この手順はVersion 4.0以降のものです。**

※pipenvをインストールしていない場合は最初にインストールしてください：```pip install pipenv```

※デフォルトとして、Postgresqlを取り扱うようになっていますが、MySQLを使用したい場合は、お手数ですがPipfileにある```psycopg2```を、
```mysqlclient```に置き換えてください。そしてconfig.tomlのdatabaseセクションにあるmodeをmysqlに変更して設定してください。

1. pipenvの環境を作ります。プロジェクトのルートディレクトリで実行してください。

   ```PIPENV_VENV_IN_PROJECT=true pipenv --python 3```

2. 必要パッケージをインストールします。手順１と同様のディレクトリで実行します。

   ```pipenv install```

3. config.tomlを設定する

   config/config.sample.toml を参考にして設定してください。

4. マイグレート（データベースの初期化）を行います。

   ```pipenv run migrate```

5. KotohiraYu.pyを実行する（もしくは```pipenv run start```を実行）

これだけですっ！

※systemdに登録しておくと便利です

## こちらで運用しています（本家アカウント）

[@Yu@best-friends.chat](https://best-friends.chat/@Yu)

## 注意事項など

- Python 3以降で動作します。Python 2は動作保証外です。

- CPU負荷がそこそこ高いため、systemdに登録する場合はCPU使用制限を設けることを推奨します。

- Mastodon用botシステムです。MisskeyなどのSNSには対応しておりません。

- Linuxでの動作を想定した設計になっているため、その他のOSでは上手く動作しない可能性がありますのでご注意ください。

- ユーザーのアカウント画像の絵文字が使用できるインスタンスを使用しています。
  そのため、その機能がついていないインスタンスの場合はお手数ですが適宜調節をお願いいたします。

- 連合アカウントには対応していません。ローカルオンリーです。

- 機能の要望やバグ修正などはMastodonなどのActivityPub対応システムで、ハッシュタグ #YuChanIssues にて受け付けております。
  もしくはIssuesかメンション([@YuzuRyo61@best-friends.chat](https://best-friends.chat/@YuzuRyo61))でどうぞ。

- *ユウちゃんをうちの子にしたかったらフォークしてくれ。*

## License

MIT License. See [LICENSE](LICENSE)
