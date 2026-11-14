from  flask import Flask
from flask import jsonify

import config
import pages
import routes_convert
import routes_quote
import errors

app = Flask(__name__)
app.config["DB_FILE"] = config.DB_FILE

app.register_blueprint(pages.bp)
app.register_blueprint(routes_convert.bp)
app.register_blueprint(routes_quote.bp)

@app.errorhandler(Exception)
def handle_unexpected_error(e):
    errors.log_error("app", str(e))
    return jsonify({"error": "Something went wrong. Please try again."}), 500

if __name__ == "__main__":
    app.run(debug=True)
    
    