import os
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

import config
import pytest

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

