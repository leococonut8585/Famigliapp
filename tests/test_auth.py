import pytest
from app import create_app

flask = pytest.importorskip("flask")


def get_client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def login(client, username, password, next_url=None):
    url = "/auth/login"
    if next_url:
        url += f"?next={next_url}"
    return client.post(url, data={"username": username, "password": password}, follow_redirects=True)


def test_login_success(test_user):
    client = get_client()
    res = login(client, test_user["username"], test_user["password"])
    assert res.status_code == 200
    assert "ログインしました".encode("utf-8") in res.data
    with client.session_transaction() as sess:
        assert sess.get("user", {}).get("username") == test_user["username"]


def test_login_failure(test_user):
    client = get_client()
    res = login(client, test_user["username"], "wrong")
    assert res.status_code == 200
    assert "ユーザー名かパスワードが違います".encode("utf-8") in res.data
    with client.session_transaction() as sess:
        assert "user" not in sess


def test_logout(test_user):
    client = get_client()
    login(client, test_user["username"], test_user["password"])
    res = client.get("/auth/logout", follow_redirects=True)
    assert res.status_code == 200
    assert "ログアウトしました".encode("utf-8") in res.data
    with client.session_transaction() as sess:
        assert "user" not in sess


def test_protected_requires_login(test_user):
    client = get_client()
    # accessing protected page redirects to login
    res = client.get("/punto/", follow_redirects=False)
    assert res.status_code == 302
    assert res.headers["Location"].startswith("/auth/login")

    # login with next parameter redirects back
    res = login(client, test_user["username"], test_user["password"], next_url="/punto/")
    assert res.status_code == 200
    assert b"Punto" in res.data
