"""Error logging for EFL – matches existing error_log columns."""

import sqlite3
from datetime import datetime
from pathlib import Path

import config


def _connect(db_file=None):
    path = db_file or config.DB_FILE
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def log_error(source, message, db_file=None):
    """
    Insert a row into error_log.
    Columns: log_id, occurred_at, source, message
    """
    try:
        conn = _connect(db_file)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO error_log (occurred_at, source, message)
            VALUES (?, ?, ?)
            """,
            (
                datetime.utcnow().isoformat(timespec="seconds"),
                source,
                message,
            ),
        )
        conn.commit()
        row_id = cur.lastrowid
        conn.close()
        return row_id
    except Exception:
        # Fallback local file if DB write fails
        with open("local_error.log", "a", encoding="utf-8") as f:
            f.write(f"{datetime.utcnow().isoformat()} | {source} | {message}\n")
        return None


def log_network_failure(detail, db_file=None):
    """Log rate-service / network failure to DB and local file."""
    log_error("network", detail, db_file=db_file)
    Path("logs").mkdir(exist_ok=True)
    with open("logs/network.log", "a", encoding="utf-8") as f:
        f.write(f"{datetime.utcnow().isoformat()} | rate service | {detail}\n")


def save_draft(user_id, form_name, form_data, db_file=None):
    """
    Cache user form data into the draft table (system failure recovery).
    form_data should be a string (e.g. JSON).
    """
    try:
        conn = _connect(db_file)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO draft (user_id, form_name, form_data, saved_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                form_name,
                form_data,
                datetime.utcnow().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
        row_id = cur.lastrowid
        conn.close()
        return row_id
    except Exception as exc:
        log_error("save_draft", str(exc), db_file=db_file)
        return None

class EFLError(Exception):
    """Base class for all application errors."""


class InputError(EFLError):
    """User entered invalid input (user fault). Shown as a 400 error."""


class RateUnavailableError(EFLError):
    """Exchange rate could not be found or refreshed (network/data fault). Shown as a 503."""
