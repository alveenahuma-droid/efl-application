import pytest
import database
import userlogin
import app as app_module

@pytest.fixture
def client(db_file):
    app_module.app.config["DB_FILE"] = db_file
    return app_module.app.test_client()

def register(client, email="ana@example.com", password="correct horse", name="Ana"):
    return client.post("/api/register", json={"name": name, "email": email, "password": password})

def login(client, email="ana@example.com", password="correct horse"):
    return client.post("/api/login", json={"email": email, "password": password})

def convert(client):
    return client.post("/api/convert", json={"amount": "500", "from": "GBP", "to": "USD"})

def saved_user_ids(db_file):
    connection = database.get_connection(db_file)
    rows = connection.execute("SELECT user_id FROM conversion_transaction").fetchall()
    connection.close()
    return [row["user_id"] for row in rows]

def test_register_creates_account_and_signs_in(client):
    assert register(client).status_code == 201
    assert client.get("/api/me").get_json()["email"] == "ana@example.com"

def test_password_is_stored_as_a_hash(client, db_file):
    register(client)
    stored = userlogin.get_user_by_email("ana@example.com", db_file)["password_hash"]
    assert "correct horse" not in stored

def test_duplicate_email_is_rejected(client):
    register(client)
    assert register(client, email="ANA@example.com").status_code == 409

def test_weak_password_and_bad_email_are_rejected(client):
    assert register(client, password="short").status_code == 400
    assert register(client, email="not-an-email").status_code == 400

def test_login_works_with_correct_password(client):
    register(client)
    client.post("/api/logout")
    assert login(client).status_code == 200
    assert client.get("/api/me").status_code == 200

def test_wrong_password_and_unknown_email_give_the_same_error(client):
    register(client)
    wrong = login(client, password="wrong password")
    unknown = login(client, email="nobody@example.com")
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.get_json() == unknown.get_json()

def test_demo_user_cannot_log_in(client):
    assert login(client, email="demo@efl.test", password="not-set").status_code == 401

def test_logout_ends_the_session(client):
    register(client)
    client.post("/api/logout")
    assert client.get("/api/me").status_code == 401

def test_conversion_is_saved_under_the_signed_in_user(client, db_file):
    register(client)
    convert(client)
    expected = userlogin.get_user_by_email("ana@example.com", db_file)["user_id"]
    assert saved_user_ids(db_file) == [expected]

def test_conversion_without_login_still_uses_the_demo_user(client, db_file):
    convert(client)
    assert saved_user_ids(db_file) == [1]

def test_quote_and_history_pages_need_login(client):
    for path in ("/quote-page", "/history-page"):
        response = client.get(path)
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/login")

def test_history_page_opens_when_signed_in(client):
    register(client)
    assert client.get("/history-page").status_code == 200

def test_login_and_register_pages_load(client):
    assert b"login-form" in client.get("/login").data
    assert b"register-form" in client.get("/register").data
