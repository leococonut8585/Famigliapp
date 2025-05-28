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


def test_compute_employee_stats():
    utils.save_events([])
    utils.add_event(date(2030, 1, 1), "s", "", "taro")
    utils.add_event(date(2030, 1, 2), "s", "", "taro")
    stats = utils.compute_employee_stats(
        start=date(2030, 1, 1), end=date(2030, 1, 3)
    )
    assert stats["taro"]["work_days"] == 2
    assert stats["taro"]["off_days"] == 1





def test_move_event_api():
    app = create_app()
    app.config["TESTING"] = True
    utils.save_events([])
    utils.add_event(date.fromisoformat("2031-01-01"), "e", "", "")
    eid = utils.load_events()[0]["id"]
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "u", "role": "user", "email": "u@example.com"}
        res = client.post(
            "/calendario/api/move",
            json={"event_id": eid, "date": "2031-01-02"},
        )
        assert res.status_code == 200
        assert res.get_json()["success"] is True
        assert utils.load_events()[0]["date"] == "2031-01-02"


def test_assign_employee_api():
    app = create_app()
    app.config["TESTING"] = True
    utils.save_events([])
    utils.add_event(date.fromisoformat("2031-02-01"), "e", "", "")
    eid = utils.load_events()[0]["id"]
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "u", "role": "user", "email": "u@example.com"}
        res = client.post(
            "/calendario/api/assign",
            json={"event_id": eid, "employee": "taro"},
        )
        assert res.status_code == 200
        assert res.get_json()["success"] is True
        assert utils.load_events()[0]["employee"] == "taro"


# --- Tests for /api/calendario/recalculate_shift_counts ---

MOCK_USERS_FOR_RECALC_TEST = {
    "admin_user": {"role": "admin", "email": "admin@example.com"},
    "user1": {"role": "user", "email": "u1@example.com"},
    "user2": {"role": "user", "email": "u2@example.com"},
    "user3": {"role": "user", "email": "u3@example.com"},
    "user4_excluded": {"role": "user", "email": "u4_excluded@example.com"},
    "user5_non_assigned": {"role": "user", "email": "u5@example.com"},
}
MOCK_EXCLUDED_USERS_FOR_RECALC_TEST = ["user4_excluded"]

def test_recalculate_shift_counts_valid_request(monkeypatch):
    app = create_app()
    app.config["TESTING"] = True
    # Patch config directly where it's imported in the routes blueprint
    monkeypatch.setattr("app.calendario.routes.config.USERS", MOCK_USERS_FOR_RECALC_TEST)
    monkeypatch.setattr("app.calendario.routes.config.EXCLUDED_USERS", MOCK_EXCLUDED_USERS_FOR_RECALC_TEST)

    with app.test_client() as client:
        # Simulate login
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}

        payload = {
            "month": "2024-07",
            "assignments": {
                "2024-07-01": ["user1", "user2"],
                "2024-07-02": ["user1"],
                "2024-07-15": ["user3"],
                "2024-07-16": ["user4_excluded"], # This assignment should be ignored for counts as user is excluded
                "2024-07-17": ["admin_user"],   # This assignment should be ignored as user is admin
            }
        }
        res = client.post("/calendario/api/calendario/recalculate_shift_counts", json=payload)

        assert res.status_code == 200
        assert res.content_type == "application/json"
        data = res.get_json()
        assert data["success"] is True

        # July has 31 days
        days_in_july = 31
        expected_counts = {
            "user1": 2,
            "user2": 1,
            "user3": 1,
            "user5_non_assigned": 0,
        }
        # admin_user and user4_excluded should not be in counts
        assert "admin_user" not in data["counts"]
        assert "user4_excluded" not in data["counts"]
        assert data["counts"] == expected_counts

        expected_off_counts = {
            "user1": days_in_july - 2,
            "user2": days_in_july - 1,
            "user3": days_in_july - 1,
            "user5_non_assigned": days_in_july - 0,
        }
        assert "admin_user" not in data["off_counts"]
        assert "user4_excluded" not in data["off_counts"]
        assert data["off_counts"] == expected_off_counts

def test_recalculate_shift_counts_invalid_month_format(monkeypatch):
    app = create_app()
    app.config["TESTING"] = True
    monkeypatch.setattr("app.calendario.routes.config.USERS", MOCK_USERS_FOR_RECALC_TEST)
    monkeypatch.setattr("app.calendario.routes.config.EXCLUDED_USERS", MOCK_EXCLUDED_USERS_FOR_RECALC_TEST)

    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        
        payload = {"month": "2024/07", "assignments": {}}
        res = client.post("/calendario/api/calendario/recalculate_shift_counts", json=payload)
        assert res.status_code == 400
        data = res.get_json()
        assert data["success"] is False
        assert "Invalid month format" in data["error"]

        payload = {"month": "July-2024", "assignments": {}}
        res = client.post("/calendario/api/calendario/recalculate_shift_counts", json=payload)
        assert res.status_code == 400
        data = res.get_json()
        assert data["success"] is False
        assert "Invalid month format" in data["error"]


def test_recalculate_shift_counts_missing_payload_keys(monkeypatch):
    app = create_app()
    app.config["TESTING"] = True
    monkeypatch.setattr("app.calendario.routes.config.USERS", MOCK_USERS_FOR_RECALC_TEST)
    monkeypatch.setattr("app.calendario.routes.config.EXCLUDED_USERS", MOCK_EXCLUDED_USERS_FOR_RECALC_TEST)

    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}

        # Missing 'month'
        payload_missing_month = {"assignments": {}}
        res = client.post("/calendario/api/calendario/recalculate_shift_counts", json=payload_missing_month)
        assert res.status_code == 400
        data = res.get_json()
        assert data["success"] is False
        assert "Missing or invalid month string" in data["error"]

        # Missing 'assignments'
        payload_missing_assignments = {"month": "2024-07"}
        res = client.post("/calendario/api/calendario/recalculate_shift_counts", json=payload_missing_assignments)
        assert res.status_code == 400
        data = res.get_json()
        assert data["success"] is False
        assert "Missing or invalid assignments data" in data["error"]

def test_recalculate_shift_counts_empty_assignments_valid(monkeypatch):
    app = create_app()
    app.config["TESTING"] = True
    monkeypatch.setattr("app.calendario.routes.config.USERS", MOCK_USERS_FOR_RECALC_TEST)
    monkeypatch.setattr("app.calendario.routes.config.EXCLUDED_USERS", MOCK_EXCLUDED_USERS_FOR_RECALC_TEST)
    
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}

        payload = {"month": "2024-03", "assignments": {}} # March has 31 days
        res = client.post("/calendario/api/calendario/recalculate_shift_counts", json=payload)
        assert res.status_code == 200
        data = res.get_json()
        assert data["success"] is True
        days_in_march = 31
        expected_counts = {
            "user1": 0, "user2": 0, "user3": 0, "user5_non_assigned": 0,
        }
        assert data["counts"] == expected_counts
        expected_off_counts = {
             "user1": days_in_march, "user2": days_in_march, "user3": days_in_march, "user5_non_assigned": days_in_march,
        }
        assert data["off_counts"] == expected_off_counts


def test_recalculate_shift_counts_unauthenticated():
    app = create_app()
    app.config["TESTING"] = True
    # No monkeypatching of config needed as auth should fail before that logic is hit
    with app.test_client() as client:
        payload = {"month": "2024-07", "assignments": {}}
        res = client.post("/calendario/api/calendario/recalculate_shift_counts", json=payload)
        # Expecting redirect to login page
        assert res.status_code == 302 
        assert "auth/login" in res.headers["Location"]


