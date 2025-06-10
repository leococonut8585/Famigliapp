import os
import tempfile
from datetime import date, timedelta
from pathlib import Path

import config
import pytest

flask = pytest.importorskip("flask")

from app import create_app
from app.Seminario import utils


def setup_module(module):
    global _tmpdir
    _tmpdir = tempfile.TemporaryDirectory()
    config.SEMINARIO_FILE = os.path.join(_tmpdir.name, "seminario.json")
    utils.SEMINARIO_PATH = Path(config.SEMINARIO_FILE)


def teardown_module(module):
    _tmpdir.cleanup()


def test_schedule_and_feedback():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        res = client.post(
            "/seminario/schedule",
            data={"date": "2025-01-01", "title": "piano"},
            follow_redirects=True,
        )
        assert res.status_code == 200
        assert "登録しました".encode("utf-8") in res.data
        entry_id = utils.load_entries()[0]["id"]
        res = client.post(
            f"/seminario/feedback/{entry_id}",
            data={"body": "good"},
            follow_redirects=True,
        )
        assert res.status_code == 200
        assert "投稿しました".encode("utf-8") in res.data
        entry = utils.load_entries()[0]
        assert entry["feedback"] == "good"


def test_pending_feedback_notification():
    past = date.today() - timedelta(days=1)
    utils.add_schedule("u1", past, "guitar")
    pending = utils.pending_feedback(date.today())
    assert len(pending) == 1
    utils.add_feedback(pending[0]["id"], "done")
    assert utils.pending_feedback(date.today()) == []

