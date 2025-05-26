import os
import tempfile
from pathlib import Path

import config
import pytest

flask = pytest.importorskip("flask")

from datetime import date

from app import create_app
from app import utils as app_utils
from app.calendario import utils


def setup_module(module):
    global _tmpdir
    _tmpdir = tempfile.TemporaryDirectory()
    config.CALENDAR_FILE = os.path.join(_tmpdir.name, "events.json")
    config.CALENDAR_RULES_FILE = os.path.join(_tmpdir.name, "rules.json")
    utils.EVENTS_PATH = Path(config.CALENDAR_FILE)
    utils.RULES_PATH = Path(config.CALENDAR_RULES_FILE)
    utils.save_rules({"max_consecutive_days": 5, "min_staff_per_day": 1})


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
            data={"date": "2025-01-01", "title": "休暇", "description": "", "employee": "taro"},
            follow_redirects=True,
        )
        assert res.status_code == 200
        assert "追加しました".encode("utf-8") in res.data
        res = client.get("/calendario/")
        assert "休暇".encode("utf-8") in res.data
        assert "taro".encode("utf-8") in res.data


def test_delete_event_route():
    app = create_app()
    app.config["TESTING"] = True
    utils.add_event(date.fromisoformat("2025-02-01"), "test", "", "staff")
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
    utils.add_event(date.fromisoformat("2025-03-01"), "nodel", "", "staff")
    event_id = utils.load_events()[0]["id"]
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        res = client.get(f"/calendario/delete/{event_id}")
        assert res.status_code == 302
        follow = client.get(res.headers["Location"])
        assert "権限がありません".encode("utf-8") in follow.data
        assert len(utils.load_events()) == 1


def test_move_event_route():
    app = create_app()
    app.config["TESTING"] = True
    utils.add_event(date.fromisoformat("2025-04-01"), "shift", "", "hanako")
    event_id = utils.load_events()[0]["id"]
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        res = client.post(
            f"/calendario/move/{event_id}",
            data={"date": "2025-04-02"},
            follow_redirects=True,
        )
        assert res.status_code == 200
        assert utils.load_events()[0]["date"] == "2025-04-02"


class DummySMTP:
    def __init__(self, *args, **kwargs):
        self.sent = []
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        pass
    def send_message(self, msg):
        self.sent.append(msg)


def test_rule_violation_sends_email(monkeypatch):
    dummy = DummySMTP()
    monkeypatch.setattr(app_utils.smtplib, "SMTP", lambda *a, **k: dummy)
    utils.save_rules({"max_consecutive_days": 1, "min_staff_per_day": 2})
    utils.add_event(date.fromisoformat("2025-05-01"), "w1", "", "taro")
    utils.add_event(date.fromisoformat("2025-05-02"), "w2", "", "taro")
    assert len(dummy.sent) > 0


def test_forbidden_pair(monkeypatch):
    dummy = DummySMTP()
    monkeypatch.setattr(app_utils.smtplib, "SMTP", lambda *a, **k: dummy)
    utils.save_events([])
    utils.save_rules(
        {
            "max_consecutive_days": 5,
            "min_staff_per_day": 1,
            "forbidden_pairs": [["taro", "hanako"]],
        }
    )
    utils.add_event(date.fromisoformat("2025-06-01"), "s1", "", "taro")
    utils.add_event(date.fromisoformat("2025-06-01"), "s2", "", "hanako")
    assert len(dummy.sent) > 0


def test_required_pair(monkeypatch):
    dummy = DummySMTP()
    monkeypatch.setattr(app_utils.smtplib, "SMTP", lambda *a, **k: dummy)
    utils.save_events([])
    utils.save_rules(
        {
            "max_consecutive_days": 5,
            "min_staff_per_day": 1,
            "required_pairs": [["taro", "hanako"]],
        }
    )
    utils.add_event(date.fromisoformat("2025-07-01"), "s1", "", "taro")
    assert len(dummy.sent) > 0


def test_required_attribute(monkeypatch):
    dummy = DummySMTP()
    monkeypatch.setattr(app_utils.smtplib, "SMTP", lambda *a, **k: dummy)
    utils.save_events([])
    utils.save_rules(
        {
            "max_consecutive_days": 5,
            "min_staff_per_day": 1,
            "required_attributes": {"A": 1},
            "employee_attributes": {"taro": "B"},
        }
    )
    utils.add_event(date.fromisoformat("2025-08-01"), "s1", "", "taro")
    assert len(dummy.sent) > 0

