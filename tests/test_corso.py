import os
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
import io

import config
import pytest

flask = pytest.importorskip("flask")

from app import create_app
from app.corso import utils


def setup_module(module):
    global _tmpdir
    _tmpdir = tempfile.TemporaryDirectory()
    config.CORSO_FILE = os.path.join(_tmpdir.name, "corso.json")
    utils.CORSO_PATH = Path(config.CORSO_FILE)


def teardown_module(module):
    _tmpdir.cleanup()


def test_add_and_list():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        res = client.post(
            "/corso/add",
            data={"title": "t", "body": "b", "end_date": ""},
            follow_redirects=True,
        )
        assert res.status_code == 200
        assert "投稿しました".encode("utf-8") in res.data
        res = client.get("/corso/")
        assert b"t" in res.data


def test_delete_route():
    app = create_app()
    app.config["TESTING"] = True
    utils.add_post("admin", "title", "body")
    post_id = utils.load_posts()[0]["id"]
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "a@example.com"}
        res = client.get(f"/corso/delete/{post_id}", follow_redirects=True)
        assert res.status_code == 200
        assert utils.load_posts() == []


def test_expired_hidden_for_user():
    app = create_app()
    app.config["TESTING"] = True
    past = datetime.now() - timedelta(days=2)
    utils.add_post("admin", "old", "body", past.date())
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        res = client.get("/corso/")
        assert b"old" not in res.data
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "a@example.com"}
        res = client.get("/corso/")
        assert b"old" in res.data


def test_filter_posts_case_insensitive():
    utils.save_posts([])
    utils.add_post("admin", "Hello", "World")
    res = utils.filter_posts(keyword="hello")
    assert len(res) == 1
    assert res[0]["title"] == "Hello"


def test_reject_invalid_extension():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        data = {"title": "t", "body": "b", "end_date": "", "attachment": (io.BytesIO(b"x"), "bad.exe")}
        res = client.post("/corso/add", data=data, follow_redirects=True)
        assert "許可されていないファイル形式です".encode("utf-8") in res.data
        assert utils.load_posts() == []


def test_reject_large_file():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        big = io.BytesIO(b"x" * (10 * 1024 * 1024 + 1))
        data = {"title": "t", "body": "b", "end_date": "", "attachment": (big, "big.txt")}
        res = client.post("/corso/add", data=data, follow_redirects=True)
        assert "ファイルサイズが大きすぎます".encode("utf-8") in res.data
        assert utils.load_posts() == []

