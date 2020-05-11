from flask import Flask, request, jsonify
from flask_jwt import JWT, jwt_required

from Yu.config import config
from Yu.database import DATABASE
from Yu.models import user_memos
from Yu.webapi_lib import authenticate, identity, model_list, model_get

app = Flask(__name__)

app.config["SECRET_KEY"] = config["webapi"]["secret"]
app.config["JSON_AS_ASCII"] = False

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
    return model_list(user_memos)

@app.route("/user_memo/<memo_time>", methods=["GET"])
def get_userMemo(memo_time=None):
    return model_get(user_memos, user_memos.memo_time, memo_time)

if __name__ == "__main__":
    app.run()
