# EFL Investment & Currency Web Application

Flask + SQLite web application for Enomy-Finances Limited (EFL), built by PDS (BTEC HND Computing, Unit 22).

## Requirements
Python 3.12 and Git.

## Install and run
```
git clone https://github.com/alveenahuma-droid/efl-application
cd efl-application
python -m venv .venv
.venv\Scripts\activate          # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
python init_db.py               # creates and seeds efl.db
flask --app app run --debug     # open http://127.0.0.1:5000
pytest -v                       # run the automated tests
```
For anything other than local use, set a long random `EFL_SECRET_KEY` environment variable.

## Settings (config.py)
DB_FILE, LOG_DIR, CACHE_DIR, MIN_TRANSACTION / MAX_TRANSACTION (300 / 5,000), CURRENCIES,
FEE_BANDS and BASE_FEE_PERCENT, SAMPLE_RATES_TO_USD, PLANS, TAX_RULES, DEMO_USER_ID.

## Current status
Working: currency conversion with Annexe A limits and fee bands, accounts (register, sign in, sign out), stored transactions.
Not yet built: savings quotes and recommendation, error log to database, network log file, data caching, live exchange rates.
