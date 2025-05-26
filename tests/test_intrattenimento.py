import os
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

import config
import pytest
import io

flask = pytest.importorskip("flask")

from app import create_app
from app.intrattenimento import utils


def setup_module(module):
    global _tmpdir
    _tmpdir = tempfile.TemporaryDirectory()
    config.INTRATTENIMENTO_FILE = os.path.join(_tmpdir.name, "intrattenimento.json")
    utils.INTRATTENIMENTO_PATH = Path(config.INTRATTENIMENTO_FILE)


def teardown_module(module):
    _tmpdir.cleanup()


def test_add_and_list():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        res = client.post(
            "/intrattenimento/add",
            data={"title": "t", "body": "b", "end_date": ""},
            follow_redirects=True,
        )
        assert res.status_code == 200
        assert "投稿しました".encode("utf-8") in res.data
        res = client.get("/intrattenimento/")
        assert b"t" in res.data


def test_delete_route():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "a@example.com"}
        utils.add_post("admin", "title", "body")
        post_id = utils.load_posts()[0]["id"]
        res = client.get(f"/intrattenimento/delete/{post_id}", follow_redirects=True)
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
        res = client.get("/intrattenimento/")
        assert b"old" not in res.data
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "a@example.com"}
        res = client.get("/intrattenimento/")
        assert b"old" in res.data


def test_download_requires_valid_period(tmp_path):
    app = create_app()
    app.config["TESTING"] = True
    os.makedirs(os.path.join("static", "uploads"), exist_ok=True)
    filepath = os.path.join("static", "uploads", "file.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("x")
    past = datetime.now() - timedelta(days=1)
    utils.add_post("admin", "t", "b", past.date(), "file.txt")
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        res = client.get("/intrattenimento/download/file.txt")
        assert res.status_code == 302
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "a@example.com"}
        res = client.get("/intrattenimento/download/file.txt")
        assert res.status_code == 200


def test_filter_by_date():
    """filter_postsで日付範囲が適用されることを確認"""

    utils.save_posts([])
    utils.add_post("admin", "old", "body")
    posts = utils.load_posts()
    posts[0]["timestamp"] = (
        datetime.now() - timedelta(days=3)
    ).isoformat(timespec="seconds")
    utils.save_posts(posts)
    utils.add_post("admin", "new", "body")

    start = datetime.now() - timedelta(days=1)
    result = utils.filter_posts(start=start)
    titles = [p.get("title") for p in result]
    assert "new" in titles
    assert "old" not in titles


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
        data = {
            "title": "t",
            "body": "b",
            "end_date": "",
            "attachment": (io.BytesIO(b"x"), "malware.exe"),
        }
        res = client.post("/intrattenimento/add", data=data, follow_redirects=True)
        assert "許可されていないファイル形式です".encode("utf-8") in res.data
        assert utils.load_posts() == []


def test_reject_large_file():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        big = io.BytesIO(b"x" * (10 * 1024 * 1024 + 1))
        data = {
            "title": "t",
            "body": "b",
            "end_date": "",
            "attachment": (big, "big.txt"),
        }
        res = client.post("/intrattenimento/add", data=data, follow_redirects=True)
        assert "ファイルサイズが大きすぎます".encode("utf-8") in res.data
        assert utils.load_posts() == []

