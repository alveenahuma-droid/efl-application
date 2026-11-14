"""Savings quotes: eligibility, projections (profit, fees, tax), recommendation and saving."""

import sqlite3
from datetime import datetime
from decimal import Decimal

import config
import errors
from currency import round_money

# Plan rules from Annexe A
PLANS = {
    "basic": {
        "name": "Basic Savings Plan",
        "min_monthly": Decimal("50"),
        "min_lump": Decimal("0"),
        "max_per_year": Decimal("20000"),
        "fee_pct": Decimal("0.25"),        # monthly % on balance
        "min_return_pct": Decimal("1.2"),  # annual
        "max_return_pct": Decimal("2.4"),
    },
    "plus": {
        "name": "Savings Plan Plus",
        "min_monthly": Decimal("50"),
        "min_lump": Decimal("300"),
        "max_per_year": Decimal("30000"),
        "fee_pct": Decimal("0.3"),
        "min_return_pct": Decimal("3.0"),
        "max_return_pct": Decimal("5.5"),
    },
    "managed": {
        "name": "Managed Stock Investments",
        "min_monthly": Decimal("150"),
        "min_lump": Decimal("1000"),
        "max_per_year": None,              # no yearly cap
        "fee_pct": Decimal("1.3"),
        "min_return_pct": Decimal("4.0"),
        "max_return_pct": Decimal("23.0"),
    },
}

# Matches the plan ids in schema.sql / config.PLANS
PLAN_IDS = {"basic": 1, "plus": 2, "managed": 3}

# Tax bands per plan, applied once per time frame on profit.
# Managed bands stack: 10% on profit above 12,000 plus 20% on profit above 40,000.
TAX_BANDS = {
    "basic": [],
    "plus": [(Decimal("12000"), Decimal("10"))],
    "managed": [(Decimal("12000"), Decimal("10")), (Decimal("40000"), Decimal("20"))],
}

HORIZONS = (1, 5, 10)


def is_eligible(plan_key, lump, monthly):
    """Check plan eligibility (Flowchart C). Returns (True, "") or (False, reason)."""
    plan = PLANS.get(plan_key)
    if plan is None:
        return False, "Unknown plan"

    lump = Decimal(str(lump))
    monthly = Decimal(str(monthly))

    if monthly < plan["min_monthly"]:
        return False, f"Monthly amount below minimum ({plan['min_monthly']})"
    if plan["min_lump"] and lump < plan["min_lump"]:
        return False, f"Lump sum below minimum ({plan['min_lump']})"
    year_one = lump + monthly * 12
    if plan["max_per_year"] is not None and year_one > plan["max_per_year"]:
        return False, f"Year-one total exceeds maximum ({plan['max_per_year']})"
    return True, ""


def future_value(lump, monthly, annual_rate_pct, years, monthly_fee_pct):
    """
    Monthly model: add the contribution, add interest (annual rate / 12),
    then take the monthly fee on the current balance.
    Returns (final_balance, total_fees), both rounded to 2 d.p.
    """
    r = Decimal(str(annual_rate_pct)) / Decimal("100") / Decimal("12")
    fee_rate = Decimal(str(monthly_fee_pct)) / Decimal("100")
    balance = Decimal(str(lump))
    total_fees = Decimal("0")

    for _ in range(int(years) * 12):
        balance = balance + Decimal(str(monthly))
        balance = balance + balance * r
        month_fee = balance * fee_rate
        balance = balance - month_fee
        total_fees = total_fees + month_fee

    return round_money(balance), round_money(total_fees)


def tax_on_profit(profit, plan_key):
    """Tax once per time frame on total profit, using the plan's bands."""
    tax = Decimal("0")
    for threshold, rate in TAX_BANDS.get(plan_key, []):
        if profit > threshold:
            tax += (profit - threshold) * rate / Decimal("100")
    return round_money(tax)


def _scenario(lump, monthly, plan_key, plan, rate_key, fee_key, years):
    """Final value, fees, profit and tax for one scenario (min or max) over one horizon."""
    final, fees = future_value(lump, monthly, plan[rate_key], years, plan["fee_pct"])
    paid_in = lump + monthly * 12 * years
    profit = round_money(final - paid_in)
    tax = tax_on_profit(profit, plan_key)
    return {
        "final": final,
        "fees": fees,
        "profit": profit,
        "tax": tax,
        "after_tax": round_money(final - tax),
    }


def calculate_quote(lump, monthly, preferred_plan=None):
    """
    Build quote results for every plan and the 1 / 5 / 10 year horizons.
    Returns (results, recommended_plan_key). Recommendation ranks eligible
    plans on the 10-year maximum value after tax.
    """
    lump = Decimal(str(lump))
    monthly = Decimal(str(monthly))
    results = []

    for key, plan in PLANS.items():
        ok, reason = is_eligible(key, lump, monthly)
        if not ok:
            results.append({
                "plan_key": key,
                "plan_name": plan["name"],
                "eligible": False,
                "reason": reason,
                "projections": [],
            })
            continue

        projections = []
        for years in HORIZONS:
            low = _scenario(lump, monthly, key, plan, "min_return_pct", "fee_pct", years)
            high = _scenario(lump, monthly, key, plan, "max_return_pct", "fee_pct", years)
            projections.append({
                "years": years,
                "paid_in": str(round_money(lump + monthly * 12 * years)),
                "min_final": str(low["final"]),
                "max_final": str(high["final"]),
                "min_fees": str(low["fees"]),
                "max_fees": str(high["fees"]),
                "min_profit": str(low["profit"]),
                "max_profit": str(high["profit"]),
                "min_tax": str(low["tax"]),
                "max_tax": str(high["tax"]),
            })

        results.append({
            "plan_key": key,
            "plan_name": plan["name"],
            "eligible": True,
            "reason": "",
            "projections": projections,
        })

    best_key, best_value = None, Decimal("-1")
    for r in results:
        if not r["eligible"]:
            continue
        ten = next(p for p in r["projections"] if p["years"] == 10)
        after_tax = Decimal(ten["max_final"]) - Decimal(ten["max_tax"])
        if after_tax > best_value:
            best_value, best_key = after_tax, r["plan_key"]

    if preferred_plan in PLANS:
        ok, _ = is_eligible(preferred_plan, lump, monthly)
        if ok:
            best_key = preferred_plan

    return results, best_key


def _connect(db_file=None):
    conn = sqlite3.connect(db_file or config.DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def save_quote(user_id, lump, monthly, plan_key, recommended_key, results, db_file=None):
    """
    Store one quote for a signed-in user: a row in quote, and six rows in
    quote_result (min and max for 1, 5 and 10 years) for the chosen plan.
    Returns the new quote_id, or None if saving failed.
    """
    chosen = next((r for r in results if r["plan_key"] == plan_key and r["eligible"]), None)
    if chosen is None:
        return None
    conn = None
    try:
        conn = _connect(db_file)
        cur = conn.execute(
            """INSERT INTO quote (user_id, plan_id, recommended_plan_id, lump_sum,
                                  monthly_amount, is_saved, created_at)
               VALUES (?, ?, ?, ?, ?, 1, ?)""",
            (
                user_id,
                PLAN_IDS[plan_key],
                PLAN_IDS.get(recommended_key),
                float(lump),
                float(monthly),
                datetime.utcnow().isoformat(timespec="seconds"),
            ),
        )
        quote_id = cur.lastrowid
        for p in chosen["projections"]:
            for scenario in ("min", "max"):
                conn.execute(
                    """INSERT INTO quote_result (quote_id, scenario, years, final_value,
                                                 total_profit, total_fees, total_tax)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        quote_id, scenario, p["years"],
                        float(p[f"{scenario}_final"]),
                        float(p[f"{scenario}_profit"]),
                        float(p[f"{scenario}_fees"]),
                        float(p[f"{scenario}_tax"]),
                    ),
                )
        conn.commit()
        return quote_id
    except Exception as exc:
        errors.log_error("quotes.save_quote", str(exc), db_file=db_file)
        return None
    finally:
        if conn is not None:
            conn.close()


def list_saved_quotes(user_id, db_file=None):
    """Saved quotes for one user, newest first."""
    conn = _connect(db_file)
    try:
        rows = conn.execute(
            """SELECT q.quote_id, q.created_at, q.lump_sum, q.monthly_amount,
                      p.name AS plan_name, r.name AS recommended_name
               FROM quote q
               JOIN investment_plan p ON p.plan_id = q.plan_id
               LEFT JOIN investment_plan r ON r.plan_id = q.recommended_plan_id
               WHERE q.user_id = ? AND q.is_saved = 1
               ORDER BY q.created_at DESC, q.quote_id DESC""",
            (user_id,),
        ).fetchall()
    finally:
        conn.close()
    return [
        {
            "quote_id": r["quote_id"],
            "created_at": r["created_at"],
            "plan_name": r["plan_name"],
            "lump_sum": r["lump_sum"],
            "monthly_amount": r["monthly_amount"],
            "recommended_name": r["recommended_name"] or "None",
        }
        for r in rows
    ]


def list_conversions(user_id, db_file=None):
    """Conversions for one user, newest first."""
    conn = _connect(db_file)
    try:
        rows = conn.execute(
            """SELECT created_at, from_currency, to_currency, amount, rate_used,
                      fee_usd, converted_amount
               FROM conversion_transaction
               WHERE user_id = ?
               ORDER BY created_at DESC, transaction_id DESC""",
            (user_id,),
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]
