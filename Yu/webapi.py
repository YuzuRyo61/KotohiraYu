from flask import Flask, request, jsonify
from flask_jwt import JWT, jwt_required

from Yu.mastodon import mastodon
from Yu.config import config
from Yu.database import DATABASE
from Yu.models import user_memos, known_users, fav_rate
from Yu.webapi_lib import authenticate, identity, model_list, model_get

app = Flask(__name__)

app.config["SECRET_KEY"] = config["webapi"]["secret"]
app.config["JSON_AS_ASCII"] = False

jwt = JWT(app, authenticate, identity)

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

@app.errorhandler(500)
def InternalError(error):
    return jsonify({
        "description": "It error occured in server",
        "error": "Internal Server Error",
        "status_code": 500
    }), 500

@app.route("/", methods=["GET"])
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
def list_userMemo():
    return model_list(user_memos)

@app.route("/user_memo/<memo_time>", methods=["GET"])
def get_userMemo(memo_time=None):
    return model_get(user_memos, user_memos.memo_time, memo_time)

@app.route("/private/known_user", methods=["GET"])
@jwt_required()
def list_knownUser():
    return model_list(known_users)

@app.route("/private/known_user/<ID>", methods=["GET"])
@jwt_required()
def get_knownUser(ID=None):
    return model_get(known_users, known_users.ID, ID)

@app.route("/private/fav_rate", methods=["GET"])
@jwt_required()
def list_favRate():
    return model_list(fav_rate)

@app.route("/private/fav_rate/<ID>", methods=["GET"])
@jwt_required()
def get_favRate(ID=None):
    return model_get(fav_rate, fav_rate.ID, ID)
