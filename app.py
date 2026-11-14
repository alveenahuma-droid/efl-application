import json
import traceback

from flask import Flask, jsonify, request

import config
import errors
import pages
import routes_auth
import routes_convert
import routes_quote

app = Flask(__name__)
app.config["DB_FILE"] = config.DB_FILE

app.register_blueprint(pages.bp)
app.register_blueprint(routes_convert.bp)
app.register_blueprint(routes_quote.bp)


@app.errorhandler(Exception)
def handle_unexpected_error(e):
    from werkzeug.exceptions import HTTPException
    if isinstance(e, HTTPException):
        return e  # 404 and similar keep their normal status
    db_file = app.config["DB_FILE"]
    errors.log_error("app", f"{request.method} {request.path}: {traceback.format_exc()[-1800:]}", db_file=db_file)
    user_id = routes_auth.signed_in_user_id()
    body = request.get_json(silent=True)
    if user_id is not None and body is not None:
        errors.save_draft(user_id, request.path, json.dumps(body), db_file=db_file)
        message = "Something went wrong. Your entries have been kept. Please try again."
    else:
        message = "Something went wrong. Please try again."
    return jsonify({"error": message}), 500


if __name__ == "__main__":
    app.run(debug=True)