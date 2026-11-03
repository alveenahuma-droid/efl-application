from decimal import Decimal                                             # For exact money maths

import config                                                           # The fee bands live in config.py
from currency import round_money                                        # Reuse the 2-decimal rounding rule

def conversion_fee_percent(amount):                                     # Which fee band does this amount fall in?
    """Return the fee percentage for this amount of the initial currency."""  # Docstring
    for threshold, percent in config.FEE_BANDS:                         # Check the highest band first
        if amount > threshold:                                         
            return percent                                              
    return config.BASE_FEE_PERCENT                                     

def conversion_fee_usd(amount, from_rate_to_usd):                       
    """Return the fee converted to US dollars, rounded to 2 decimal places."""  
    percent = conversion_fee_percent(amount)                            
    fee_in_initial = amount * percent / Decimal("100")                 
    return round_money(fee_in_initial * from_rate_to_usd)               
