from flask import Blueprint, jsonify, request

import errors
import quotes
import routes_auth

bp = Blueprint("routes_quote", __name__)

PLAN_MAP = {
    "1": "basic", "2": "plus", "3": "managed",
    "basic": "basic", "plus": "plus", "managed": "managed",
}


def _parse_request():
    """Read and map the request fields shared by quote and save."""
    data = request.get_json(silent=True) or {}
    lump = data.get("lump_sum", 0) or 0
    monthly = data.get("monthly_amount", 0) or 0
    preferred_raw = data.get("plan")
    preferred = PLAN_MAP.get(str(preferred_raw)) if preferred_raw is not None else None
    return lump, monthly, preferred


@bp.post("/api/quote")
def api_quote():
    lump, monthly, preferred = _parse_request()
    try:
        results, recommended = quotes.calculate_quote(lump, monthly, preferred)
        return jsonify({
            "results": results,
            "recommended": recommended,
            "recommended_name": quotes.PLANS[recommended]["name"] if recommended else None,
        })
    except Exception as e:
        errors.log_error("routes_quote.api_quote", str(e))
        return jsonify({"error": "Could not calculate quote. Please check your inputs."}), 400


@bp.post("/api/quotes/save")
def api_save_quote():
    user_id = routes_auth.signed_in_user_id()
    if user_id is None:
        return jsonify({"error": "Sign in to save a quote."}), 401

    lump, monthly, preferred = _parse_request()
    try:
        results, recommended = quotes.calculate_quote(lump, monthly, preferred)
    except Exception as e:
        errors.log_error("routes_quote.api_save_quote", str(e))
        return jsonify({"error": "Could not calculate quote. Please check your inputs."}), 400

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
