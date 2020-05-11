from flask import Flask, jsonify, request, abort
from flask_jwt import JWT, jwt_required, current_identity
from werkzeug.security import safe_str_cmp
from playhouse.shortcuts import model_to_dict

from Yu.config import config
from Yu.database import DATABASE
from Yu.models import user_memos

app = Flask(__name__)

app.config["SECRET_KEY"] = config["webapi"]["secret"]
app.config["JSON_AS_ASCII"] = False

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

jwt = JWT(app, authenticate, identity)

@app.errorhandler(404)
def NotFound(error):
    return jsonify({
        "error": {
            "code": "NOT_FOUND"
        }
    }), 404

@app.errorhandler(405)
def MethodNotAllowed(error):
    return jsonify({
        "error": {
            "code": "METHOD_NOT_ALLOWED"
        }
    }), 405

@app.errorhandler(500)
def InternalError(error):
    return jsonify({
        "error": {
            "code": "INTERNAL_SERVER_ERROR"
        }
    }), 500

@app.route("/user_memo", methods=["GET"])
def list_userMemo():
    q_limit = request.args.get('limit', default=-1, type=int)
    q_offset = request.args.get('offset', default=0, type=int)

    if q_limit == -1:
        memos = user_memos.select().dicts()
    else:
        memos = user_memos.select().limit(q_limit).offset(q_offset).dicts()

    return jsonify([memo for memo in memos])

@app.route("/user_memo/<memo_time>", methods=["GET"])
def get_userMemo(memo_time=None):
    memo = user_memos.get_or_none(user_memos.memo_time == memo_time)
    if memo == None:
        abort(404)
    else:
        return jsonify(model_to_dict(memo))

def WEBRUN():
    app.run(host=config["webapi"]["host"], port=config["webapi"]["port"])
