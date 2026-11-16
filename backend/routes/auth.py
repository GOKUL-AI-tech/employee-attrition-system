from functools import wraps
from flask import Blueprint, request, jsonify, current_app
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from werkzeug.security import check_password_hash
from database import get_db

bp = Blueprint("auth", __name__, url_prefix="/api/auth")
MAX_AGE = 60 * 60 * 12


def _ser():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def login_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        token = request.headers.get("Authorization", "").replace("Bearer ", "") or request.args.get("token", "")
        try:
            _ser().loads(token, max_age=MAX_AGE)
        except (BadSignature, SignatureExpired):
            return jsonify(error="Unauthorized"), 401
        return fn(*a, **kw)
    return wrapper


@bp.post("/login")
def login():
    d = request.get_json(silent=True) or {}
    u = get_db().execute("SELECT * FROM users WHERE username=?", (str(d.get("username", "")).strip(),)).fetchone()
    if not u or not check_password_hash(u["password_hash"], str(d.get("password", ""))):
        return jsonify(error="Invalid username or password"), 401
    return jsonify(token=_ser().dumps({"u": u["username"]}), user={"username": u["username"], "full_name": u["full_name"]})


@bp.get("/me")
@login_required
def me():
    return jsonify(ok=True)
