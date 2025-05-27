import pytest
import tempfile
import os
from pathlib import Path

flask = pytest.importorskip("flask")

import config
from app import create_app, utils as app_utils
from app.vote_box import utils


class DummySMTP:
    def __init__(self, *a, **k):
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
    config.VOTE_BOX_FILE = os.path.join(_tmpdir.name, "votebox.json")
    utils.VOTE_BOX_PATH = Path(config.VOTE_BOX_FILE)


def teardown_module(module):
    _tmpdir.cleanup()


def test_create_vote_and_flow(monkeypatch):
    dummy = DummySMTP()
    monkeypatch.setattr(app_utils.smtplib, "SMTP", lambda *a, **k: dummy)
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        res = client.post(
            "/vote_box/create",
            data={"title": "q", "options": "a\nb", "targets": ["user2"]},
            follow_redirects=True,
        )
        assert res.status_code == 200
        polls = utils.load_polls()
        assert polls[0]["title"] == "q"
        assert polls[0]["options"] == ["a", "b"]
        assert len(dummy.sent) == 1
        poll_id = polls[0]["id"]

        res = client.get("/vote_box/open")
        assert b"q" in res.data

        res = client.post(
            f"/vote_box/vote/{poll_id}",
            data={"choice": "0"},
            follow_redirects=True,
        )
        assert res.status_code == 200
        assert utils.load_polls()[0]["votes"]["user1"] == 0

        with client.session_transaction() as sess:
            sess["user"] = {"username": "user2", "role": "user", "email": "u2@example.com"}
        res = client.post(
            f"/vote_box/vote/{poll_id}",
            data={"choice": "1"},
            follow_redirects=True,
        )
        assert utils.load_polls()[0]["votes"]["user2"] == 1

        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        res = client.get(f"/vote_box/close/{poll_id}", follow_redirects=True)
        assert "権限がありません".encode("utf-8") in res.data

        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "a@example.com"}
        res = client.get(f"/vote_box/close/{poll_id}", follow_redirects=True)
        assert res.status_code == 200
        assert utils.load_polls()[0]["status"] == "closed"
