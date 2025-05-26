import os
import tempfile
from pathlib import Path

import config
import pytest

flask = pytest.importorskip("flask")

from datetime import date

from app import create_app
from app.calendario import utils


def setup_module(module):
    global _tmpdir
    _tmpdir = tempfile.TemporaryDirectory()
    config.CALENDAR_FILE = os.path.join(_tmpdir.name, "events.json")
    utils.EVENTS_PATH = Path(config.CALENDAR_FILE)


def teardown_module(module):
    _tmpdir.cleanup()


def test_add_and_list_event():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        res = client.post(
            "/calendario/add",
            data={"date": "2025-01-01", "title": "休暇", "description": ""},
            follow_redirects=True,
        )
        assert res.status_code == 200
        assert "追加しました".encode("utf-8") in res.data
        res = client.get("/calendario/")
        assert "休暇".encode("utf-8") in res.data


def test_delete_event_route():
    app = create_app()
    app.config["TESTING"] = True
    utils.add_event(date.fromisoformat("2025-02-01"), "test", "")
    event_id = utils.load_events()[0]["id"]
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "a@example.com"}
        res = client.get(f"/calendario/delete/{event_id}", follow_redirects=True)
        assert res.status_code == 200
        assert utils.load_events() == []


def test_delete_event_as_user():
    app = create_app()
    app.config["TESTING"] = True
    utils.add_event(date.fromisoformat("2025-03-01"), "nodel", "")
    event_id = utils.load_events()[0]["id"]
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        res = client.get(f"/calendario/delete/{event_id}")
        assert res.status_code == 302
        follow = client.get(res.headers["Location"])
        assert "権限がありません".encode("utf-8") in follow.data
        assert len(utils.load_events()) == 1

