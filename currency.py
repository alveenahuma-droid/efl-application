from decimal import Decimal, ROUND_HALF_UP                              

import database                                                        

TWO_PLACES = Decimal("0.01")                                            
SIX_PLACES = Decimal("0.000001")                                        

def round_money(value):                                                 
    """Round to 2 decimal places, halves rounded up."""                 
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)           

def get_rate(from_code, to_code, db_file=None):                         
    """Return the rate from one currency to another, rounded to 6 places.""" 
    from_usd = database.get_rate_to_usd(from_code, db_file)             
    to_usd = database.get_rate_to_usd(to_code, db_file)                 
    return (from_usd / to_usd).quantize(SIX_PLACES, rounding=ROUND_HALF_UP)  

def convert(amount, rate):                                              
    """Return the converted amount rounded to 2 decimal places."""      
    return round_money(amount * rate)                                   

def refresh_rates(db_file=None):
    """
    Load live rates from config.RATE_API_URL, at most once an hour.

    The service must return JSON like {"base": "USD", "rates": {"GBP": 0.77, ...}},
    where each rate is units of that currency per 1 USD.

    Returns None when the rates are fine or no live service is configured.
    A failed refresh is always logged (database and logs/network.log). A warning
    is returned only if the newest live rate is more than 24 hours old.
    """
    import json
    import urllib.request
    import config
    import database
    import errors

    if not config.RATE_API_URL:
        return None
    if database.has_recent_live_rate(60, db_file):   # Already refreshed in the last hour
        return None
    try:
        with urllib.request.urlopen(config.RATE_API_URL, timeout=config.RATE_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
        rates = payload["rates"]
        database.save_live_rates(
            {code: Decimal("1") / Decimal(str(rates[code])) for code in config.CURRENCIES if code != "USD"},
            db_file,
        )
        return None
    except Exception as problem:
        errors.log_network_failure(f"rate refresh failed: {problem}", db_file=db_file)
        if database.has_recent_live_rate(24 * 60, db_file):   # Live rates still fresh enough: no warning
            return None
        return "Live rates are unavailable, so the last saved rate is used and may be out of date."


def stale_rate_warning(db_file=None):
    """Quick check with no network call: warn only if the newest live rate is more than 24 hours old."""
    import database
    if database.has_recent_live_rate(24 * 60, db_file):
        return None
    return "Live rates are unavailable, so the last saved rate is used and may be out of date."
