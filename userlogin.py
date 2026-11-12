import sqlite3

import database                                    
from errors import InputError

class EmailTakenError(InputError):
    """An account with this email already exists."""

def create_user(name, email, password_hash, db_file=None):
    """Insert a user and return the new id. Raises EmailTakenError if the email exists."""
    connection = database.get_connection(db_file)
    try:
        cursor = connection.execute(
            "INSERT INTO user (name, email, password_hash) VALUES (?, ?, ?)",   # Only the hash is stored, never the password
            (name, email, password_hash),
        )
        connection.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:                 # The UNIQUE rule on email was broken
        raise EmailTakenError("An account with this email already exists.")
    finally:
        connection.close()

def get_user_by_email(email, db_file=None):
    """Used at sign-in. Returns a dictionary, or None."""
    connection = database.get_connection(db_file)
    try:
        row = connection.execute(
            "SELECT user_id, name, email, password_hash FROM user WHERE email = ?", (email,)
        ).fetchone()
    finally:
        connection.close()
    return dict(row) if row else None

def get_user_by_id(user_id, db_file=None):
    """Used to show the name in the page header. Returns a dictionary, or None."""
    connection = database.get_connection(db_file)
    try:
        row = connection.execute(
            "SELECT user_id, name, email FROM user WHERE user_id = ?", (user_id,)
        ).fetchone()
    finally:
        connection.close()
    return dict(row) if row else None
