import os
import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest

flask = pytest.importorskip("flask")

import config
from app.seminario import utils, tasks


def setup_module(module):
    global _tmpdir
    _tmpdir = tempfile.TemporaryDirectory()
    config.SEMINARIO_FILE = os.path.join(_tmpdir.name, "seminario.json")
    utils.SEMINARIO_PATH = Path(config.SEMINARIO_FILE)


def teardown_module(module):
    _tmpdir.cleanup()


def test_notify_pending_feedback(monkeypatch):
    past = date.today() - timedelta(days=1)
    utils.add_schedule("user1", past, "guitar")

    sent = []

    def dummy_send(subject, body, to):
        sent.append((subject, body, to))

    monkeypatch.setattr(tasks, "send_email", dummy_send)

    notified = tasks.notify_pending_feedback(date.today() - timedelta(days=2), date.today())
    assert len(notified) == 1
    assert sent and sent[0][2] == config.USERS["user1"]["email"]

    # since after lesson date -> no notification
    sent.clear()
    notified = tasks.notify_pending_feedback(date.today(), date.today())
    assert notified == []
    assert sent == []
