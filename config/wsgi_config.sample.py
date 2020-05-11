# ユウちゃんのバックエンドWebAPIを使用する場合は設定してください
# 詳しい設定はgunicornのドキュメントを参照してください↓
# https://docs.gunicorn.org/en/stable/settings.html

bind = "0.0.0.0:8787"
proc_name = "KotohiraYu"
workers = 1
worker_connections = 1000
reload = False
loglevel = "info"
socket_path = "unix:/tmp/kotohirayu-web.sock"
bind = socket_path
