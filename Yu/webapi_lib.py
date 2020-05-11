from flask import request, abort, jsonify
from playhouse.shortcuts import model_to_dict
from werkzeug.security import safe_str_cmp

from Yu.config import config

class WebUser:
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def __str__(self):
        return "WebUser(username='%s')" % self.username

users = []
for index, user in enumerate(config["webapi"]["user"]):
    users.append(
        WebUser(index + 1, user["username"], user["password"])
    )

username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}

def authenticate(username, password):
    user = username_table.get(username, None)
    if user and safe_str_cmp(user.password.encode("utf-8"), password.encode("utf-8")):
        return user

def identity(payload):
    user_id = payload["identity"]
    return userid_table.get(user_id, None)

def model_list(model):
    q_limit = request.args.get('limit', default=-1, type=int)
    q_offset = request.args.get('offset', default=0, type=int)

    if q_limit == -1:
        memos = model.select().dicts()
    else:
        memos = model.select().limit(q_limit).offset(q_offset).dicts()

    return jsonify([memo for memo in memos])

def model_get(model, column, query):
    data = model.get_or_none(column == query)
    if data == None:
        abort(404)
    else:
        return jsonify(model_to_dict(data))
