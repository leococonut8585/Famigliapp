import os
import tempfile
from datetime import date
from pathlib import Path

import pytest

flask = pytest.importorskip("flask")

import config
from app.principessina import utils, tasks


def setup_module(module):
    global _tmpdir
    _tmpdir = tempfile.TemporaryDirectory()
    config.PRINCIPESSINA_FILE = os.path.join(_tmpdir.name, "principessina.json")
    utils.PRINCIPESSINA_PATH = Path(config.PRINCIPESSINA_FILE)


def teardown_module(module):
    _tmpdir.cleanup()


def test_notify_missing_posts(monkeypatch):
    today = date.today()
    utils.add_post("user1", "report", None)
    sent = []

    def dummy_send(subject, body, to):
        sent.append((subject, body, to))

    monkeypatch.setattr(tasks, "send_email", dummy_send)

    notified = tasks.notify_missing_posts(today)
    # user1 has posted, user2 has not
    assert "user2" in notified
    assert any(to == config.USERS["user2"]["email"] for _, _, to in sent)
    # admin should also be notified if not posted (since config lists admin)
    assert "admin" in notified
