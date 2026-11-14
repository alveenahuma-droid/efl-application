from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request

import errors
import quotes
import routes_auth
from errors import InputError

bp = Blueprint("routes_quote", __name__)

PLAN_MAP = {
    "1": "basic", "2": "plus", "3": "managed",
    "basic": "basic", "plus": "plus", "managed": "managed",
}


def _money(value, field):
    """Read a money amount typed by the user. Raises InputError with a clear message."""
    text = str(value if value not in (None, "") else "0").replace(",", "").strip()
    try:
        amount = Decimal(text)
    except InvalidOperation:
        raise InputError(f"{field} must be a number, for example 5000 or 5000.00.")
    if not amount.is_finite():
        raise InputError(f"{field} must be a number, for example 5000 or 5000.00.")
    if amount < 0:
        raise InputError(f"{field} cannot be negative.")
    if amount.as_tuple().exponent < -2:
        raise InputError(f"{field} can have at most two decimal places.")
    return amount


def _parse_request():
    """Read and check the fields shared by quote and save. Raises InputError for bad input."""
    data = request.get_json(silent=True) or {}
    lump = _money(data.get("lump_sum"), "Lump sum")
    monthly = _money(data.get("monthly_amount"), "Monthly amount")
    preferred_raw = data.get("plan")
    preferred = PLAN_MAP.get(str(preferred_raw)) if preferred_raw is not None else None
    return lump, monthly, preferred


@bp.post("/api/quote")
def api_quote():
    try:
        lump, monthly, preferred = _parse_request()
    except InputError as error:
        return jsonify({"error": str(error)}), 400  # user fault: show the message, do not log it
    try:
        results, recommended = quotes.calculate_quote(lump, monthly, preferred)
        return jsonify({
            "results": results,
            "recommended": recommended,
            "recommended_name": quotes.PLANS[recommended]["name"] if recommended else None,
        })
    except Exception as e:
        errors.log_error("routes_quote.api_quote", str(e))  # internal fault: log it
        return jsonify({"error": "Could not calculate quote. Please try again."}), 500


@bp.post("/api/quotes/save")
def api_save_quote():
    user_id = routes_auth.signed_in_user_id()
    if user_id is None:
        return jsonify({"error": "Sign in to save a quote."}), 401

    try:
        lump, monthly, preferred = _parse_request()
    except InputError as error:
        return jsonify({"error": str(error)}), 400

    try:
        results, recommended = quotes.calculate_quote(lump, monthly, preferred)
    except Exception as e:
        errors.log_error("routes_quote.api_save_quote", str(e))
        return jsonify({"error": "Could not calculate quote. Please try again."}), 500

    chosen = preferred or recommended
    if chosen is None:
        return jsonify({"error": "No plan is available for these amounts, so there is nothing to save."}), 400

    chosen_result = next(r for r in results if r["plan_key"] == chosen)
    if not chosen_result["eligible"]:
        return jsonify({"error": chosen_result["reason"] + "."}), 400

    quote_id = quotes.save_quote(user_id, lump, monthly, chosen, recommended, results)
    if quote_id is None:
        return jsonify({"error": "The quote could not be saved. Please try again."}), 500
    return jsonify({"quote_id": quote_id}), 201


@bp.get("/api/quotes")
def api_list_quotes():
    user_id = routes_auth.signed_in_user_id()
    if user_id is None:
        return jsonify({"error": "Sign in to continue."}), 401
    return jsonify(quotes.list_saved_quotes(user_id))


@bp.get("/api/transactions")
def api_list_transactions():
    user_id = routes_auth.signed_in_user_id()
    if user_id is None:
        return jsonify({"error": "Sign in to continue."}), 401
    return jsonify(quotes.list_conversions(user_id))