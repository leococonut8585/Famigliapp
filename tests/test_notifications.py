import os
import tempfile
from pathlib import Path

import config
from app import create_app, utils
import pytest

flask = pytest.importorskip("flask")

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
    config.POINTS_FILE = os.path.join(_tmpdir.name, "points.json")
    config.POINTS_HISTORY_FILE = os.path.join(_tmpdir.name, "points_history.json")
    config.POSTS_FILE = os.path.join(_tmpdir.name, "posts.json")

    utils.POINTS_PATH = Path(config.POINTS_FILE)
    utils.POINTS_HISTORY_PATH = Path(config.POINTS_HISTORY_FILE)
    utils.POSTS_PATH = Path(config.POSTS_FILE)

    utils.save_points({"user1": {"A": 0, "O": 0}})


def teardown_module(module):
    _tmpdir.cleanup()


def test_points_change_sends_email(monkeypatch):
    dummy = DummySMTP()
    monkeypatch.setattr(utils.smtplib, "SMTP", lambda *a, **k: dummy)
    utils.log_points_change("user1", 1, 0)
    assert len(dummy.sent) == 1


def test_post_add_sends_email(monkeypatch):
    dummy = DummySMTP()
    monkeypatch.setattr(utils.smtplib, "SMTP", lambda *a, **k: dummy)
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        res = client.post("/posts/add", data={"category": "news", "text": "hello"}, follow_redirects=True)
        assert res.status_code == 200
    assert len(dummy.sent) == len(config.USERS)


def test_line_notification(monkeypatch):
    dummy = DummySMTP()
    monkeypatch.setattr(utils.smtplib, "SMTP", lambda *a, **k: dummy)
    msgs = []

    def dummy_line(msg):
        msgs.append(msg)

    monkeypatch.setattr(utils, "send_line_notify", dummy_line)
    config.LINE_NOTIFY_TOKEN = "token"
    utils.log_points_change("user1", 2, 0)
    assert msgs and "Points updated" in msgs[0]
    config.LINE_NOTIFY_TOKEN = ""


def test_pushbullet_notification(monkeypatch):
    dummy = DummySMTP()
    monkeypatch.setattr(utils.smtplib, "SMTP", lambda *a, **k: dummy)
    pushes = []

    def dummy_push(title, body):
        pushes.append((title, body))

    monkeypatch.setattr(utils, "send_pushbullet_notify", dummy_push)
    config.PUSHBULLET_TOKEN = "token"
    utils.log_points_change("user1", 3, 0)
    assert pushes and "Points updated" in pushes[0][0]
    config.PUSHBULLET_TOKEN = ""
