"""The HTML pages."""
from flask import Blueprint, render_template

import routes_auth

bp = Blueprint("pages", __name__)
bp.register_blueprint(routes_auth.bp)        

@bp.route("/")
def index():
    return render_template("index.html")

@bp.route("/login")
def login_page():
    return render_template("login.html")

@bp.route("/register")
def register_page():
    return render_template("register.html")

@bp.route("/converter")
def converter_page():
    return render_template("converter.html")

@bp.route("/quote-page")
@routes_auth.login_required_page
def quote_page():
    return render_template("quote.html")

@bp.route("/history-page")
@routes_auth.login_required_page
def history_page():
    return render_template("history.html")
