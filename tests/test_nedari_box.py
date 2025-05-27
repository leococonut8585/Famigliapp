import os
import tempfile
from pathlib import Path

import pytest

flask = pytest.importorskip("flask")

import config
from app import create_app, utils as app_utils
from app.nedari_box import utils


class DummySMTP:
    def __init__(self, *args, **kwargs):
        self.sent = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

    def send_message(self, msg):
        self.sent.append(msg)


def setup_module(module):
    global _tmpdir
    _tmpdir = tempfile.TemporaryDirectory()
    config.NEDARI_FILE = os.path.join(_tmpdir.name, "nedari.json")
    utils.NEDARI_PATH = Path(config.NEDARI_FILE)


def teardown_module(module):
    _tmpdir.cleanup()


def test_add_and_list_nedari(monkeypatch):
    dummy = DummySMTP()
    monkeypatch.setattr(app_utils.smtplib, "SMTP", lambda *a, **k: dummy)
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        res = client.post(
            "/nedari_box/add",
            data={"body": "need", "targets": ["user2"], "visibility": "all"},
            follow_redirects=True,
        )
        assert res.status_code == 200
        posts = utils.load_posts()
        assert posts[0]["body"] == "need"
        assert posts[0]["targets"] == ["user2"]
        assert posts[0]["visibility"] == "all"
        assert len(dummy.sent) == len(config.USERS)
        res = client.get("/nedari_box/")
        assert b"need" in res.data


def test_visibility_limitation():
    utils.save_posts([
        {"id": 1, "author": "user1", "body": "secret", "targets": ["user2"], "visibility": "admins", "timestamp": "t"}
    ])
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user2", "role": "user", "email": "u2@example.com"}
        res = client.get("/nedari_box/")
        assert b"secret" not in res.data
        with client.session_transaction() as sess:
            sess["user"] = {"username": "leo", "role": "admin", "email": "leo@example.com"}
        res = client.get("/nedari_box/")
        assert b"secret" in res.data
