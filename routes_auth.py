"""Register, sign in and sign out. Attached to the pages blueprint, so app.py is not changed."""
import os
import re
from functools import wraps

from flask import Blueprint, current_app, jsonify, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

import config
import security
import userlogin
from errors import InputError

bp = Blueprint("auth", __name__)

SECRET_KEY = os.environ.get("EFL_SECRET_KEY", "dev-only-change-me")     # Set EFL_SECRET_KEY to a long random value for real use
MIN_PASSWORD_LENGTH = 8
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
DUMMY_HASH = generate_password_hash("not-a-real-password")              # Checked for unknown emails, so timing does not reveal them
BAD_LOGIN = "Email or password is incorrect."                           # Same message for a wrong password and an unknown email

def signed_in_user_id():
    """The id of the person who is signed in, or None."""
    return session.get("user_id")

def user_or_demo():
    """Replaces security.current_user_id at start-up: the signed-in user, else the demo user as before."""
    return session.get("user_id") or config.DEMO_USER_ID

@bp.record_once
def set_up(state):
    """Runs once when the app starts, so app.py does not need to change."""
    app = state.app
    if not app.config.get("SECRET_KEY"):                    # Flask starts with None, so check for empty
        app.config["SECRET_KEY"] = SECRET_KEY
    app.config["SESSION_COOKIE_HTTPONLY"] = True            # JavaScript cannot read the login cookie
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"           # Other sites cannot send it with their requests
    security.current_user_id = user_or_demo                 # routes_convert calls security.current_user_id(), so conversions are saved under the signed-in user

@bp.app_context_processor
def inject_user():
    """Make the signed-in name available to every template."""
    user_id = signed_in_user_id()
    user = userlogin.get_user_by_id(user_id, current_app.config["DB_FILE"]) if user_id else None
    return {"signed_in": user is not None, "user_name": user["name"] if user else None}

def login_required_page(view):
    """For HTML pages: send visitors who are not signed in to the login page."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if signed_in_user_id() is None:
            return redirect(url_for("pages.login_page"))
        return view(*args, **kwargs)
    return wrapper

def check_name(text):
    name = str(text or "").strip()
    if not name or len(name) > 80:
        raise InputError("Enter your name, up to 80 characters.")
    return name

def check_email(text):
    email = str(text or "").strip().lower()
    if len(email) > 254 or not EMAIL_PATTERN.match(email):
        raise InputError("Enter a valid email address, for example name@example.com.")
    return email

def check_password(text):
    password = str(text or "")
    if len(password) < MIN_PASSWORD_LENGTH or len(password) > 128:
        raise InputError("Use a password of " + str(MIN_PASSWORD_LENGTH) + " to 128 characters.")
    return password

@bp.route("/api/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    db_file = current_app.config["DB_FILE"]
    try:
        name = check_name(data.get("name"))
        email = check_email(data.get("email"))
        password = check_password(data.get("password"))
        user_id = userlogin.create_user(name, email, generate_password_hash(password), db_file)
    except userlogin.EmailTakenError as error:
        return jsonify({"error": str(error)}), 409
    except InputError as error:
        return jsonify({"error": str(error)}), 400
    session.clear()
    session["user_id"] = user_id
    return jsonify({"user_id": user_id, "name": name}), 201

@bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email") or "").strip().lower()
    password = str(data.get("password") or "")
    user = userlogin.get_user_by_email(email, current_app.config["DB_FILE"])
    stored_hash = user["password_hash"] if user else DUMMY_HASH
    if not check_password_hash(stored_hash, password) or user is None:
        return jsonify({"error": BAD_LOGIN}), 401
    session.clear()
    session["user_id"] = user["user_id"]
    return jsonify({"user_id": user["user_id"], "name": user["name"]}), 200

@bp.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True}), 200

@bp.route("/api/me", methods=["GET"])
def me():
    user_id = signed_in_user_id()
    user = userlogin.get_user_by_id(user_id, current_app.config["DB_FILE"]) if user_id else None
    if user is None:
        return jsonify({"error": "Sign in to continue."}), 401
    return jsonify(user), 200
