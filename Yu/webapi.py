import json

from flask import Flask, request, jsonify
from flask_jwt import JWT, jwt_required
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from Yu.mastodon import mastodon
from Yu.config import config
from Yu.database import DATABASE
from Yu.models import user_memos, known_users, fav_rate, nickname
from Yu.webapi_lib import authenticate, identity, model_list, model_get

app = Flask(__name__)

app.config["SECRET_KEY"] = config["webapi"]["secret"]
app.config["JSON_AS_ASCII"] = False

jwt = JWT(app, authenticate, identity)

limiter = Limiter(app, key_func=get_remote_address, headers_enabled=True)

@app.errorhandler(404)
def NotFound(error):
    return jsonify({
        "description": "Request API is not found",
        "error": "Not Found",
        "status_code": 404
    }), 404

@app.errorhandler(405)
def MethodNotAllowed(error):
    return jsonify({
        "description": "Requested method is not allowed",
        "error": "Method Not Allowed",
        "status_code": 405
    }), 405

@app.errorhandler(429)
def TooManyRequests(error):
    return jsonify({
        "description": "The API limit has been reached",
        "limit": error.description,
        "error": "Too Many Requests",
        "status_code": 429
    }), 429

@app.errorhandler(500)
def InternalError(error):
    return jsonify({
        "description": "It error occured in server",
        "error": "Internal Server Error",
        "status_code": 500
    }), 500

@app.route("/", methods=["GET"])
@limiter.limit("60/hour;5/minute")
def api_index():
    return jsonify({
        "working_server": config["instance"]["address"],
        "features": {
            "ngword": config["features"]["ngword"],
            "voteOptout": config["features"]["voteOptout"],
            "voteOptoutTag": config["features"]["voteOptoutTag"],
            "newComerGreeting": config["features"]["newComerGreeting"]
        }
    })

@app.route("/user_memo", methods=["GET"])
@limiter.limit("120/hour")
def list_userMemo():
    query = model_list(user_memos)
    for index, _ in enumerate(query):
        try:
            query[index]["body"] = json.loads(query[index]["body"])
        except json.decoder.JSONDecodeError:
            pass
    
    return jsonify(query)

@app.route("/user_memo/<memo_time>", methods=["GET"])
@limiter.limit("120/hour")
def get_userMemo(memo_time=None):
    query = model_get(user_memos, user_memos.memo_time, memo_time)
    try:
        query["body"] = json.loads(query["body"])
    except json.decoder.JSONDecodeError:
        pass

    return jsonify(query)

@app.route("/nickname", methods=["GET"])
@limiter.limit("120/hour")
def list_nickname():
    return jsonify(model_list(nickname))

@app.route("/nickname/<ID>", methods=["GET"])
@limiter.limit("120/hour")
def get_nickname(ID=None):
    return jsonify(model_get(nickname, nickname.ID, ID))

@app.route("/stats", methods=["GET"])
@limiter.limit("60/hour")
def api_stats():
    return jsonify({
        "count": {
            "known_users": known_users.select().count(), # pylint: disable=no-value-for-parameter
            "nickname": nickname.select().count(), # pylint: disable=no-value-for-parameter
            "user_memo": user_memos.select().count() # pylint: disable=no-value-for-parameter
        }
    })

@app.route("/private/known_user", methods=["GET"])
@jwt_required()
def list_knownUser():
    return jsonify(model_list(known_users))

@app.route("/private/known_user/<ID>", methods=["GET"])
@jwt_required()
def get_knownUser(ID=None):
    return jsonify(model_get(known_users, known_users.ID, ID))

@app.route("/private/fav_rate", methods=["GET"])
@jwt_required()
def list_favRate():
    return jsonify(model_list(fav_rate))

@app.route("/private/fav_rate/<ID>", methods=["GET"])
@jwt_required()
def get_favRate(ID=None):
    return jsonify(model_get(fav_rate, fav_rate.ID, ID))
