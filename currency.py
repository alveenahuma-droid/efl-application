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
    Try to load live rates from config.RATE_API_URL. The service must return
    JSON like {"base": "USD", "rates": {"GBP": 0.77, ...}} where each rate is
    units of that currency per 1 USD.

    Returns None when everything is fine or no live service is configured.
    If the service fails, the failure is logged to the database and to
    logs/network.log, and a warning is returned so the user sees that the
    saved rate is being used. The saved rate is not replaced.
    """
    import json
    import urllib.request
    import config
    import errors

    if not config.RATE_API_URL:
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
        return "Live rates are unavailable, so the last saved rate is used and may be out of date."
