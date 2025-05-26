import tempfile
from pathlib import Path

import pytest

flask = pytest.importorskip("flask")

import config
from app import create_app, utils as app_utils
from app.scatola_capriccio import utils


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
    config.SCATOLA_SURVEY_FILE = str(Path(_tmpdir.name) / "surveys.json")
    utils.SURVEYS_PATH = Path(config.SCATOLA_SURVEY_FILE)
    config.SCATOLA_FILE = str(Path(_tmpdir.name) / "scatola.json")
    utils.SCATOLA_PATH = Path(config.SCATOLA_FILE)


def teardown_module(module):
    _tmpdir.cleanup()


def test_add_survey_and_list(monkeypatch):
    dummy = DummySMTP()
    monkeypatch.setattr(app_utils.smtplib, "SMTP", lambda *a, **k: dummy)
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "a@example.com"}
        res = client.post(
            "/scatola_capriccio/survey/add",
            data={"question": "q1", "targets": "user1,user2"},
            follow_redirects=True,
        )
        assert res.status_code == 200
        surveys = utils.load_surveys()
        assert surveys[0]["question"] == "q1"
        assert surveys[0]["targets"] == ["user1", "user2"]
        assert len(dummy.sent) == 2
        res = client.get("/scatola_capriccio/survey")
        assert b"q1" in res.data


def test_non_admin_cannot_view_survey():
    app = create_app()
    app.config["TESTING"] = True
    utils.save_surveys([
        {"id": 1, "author": "admin", "question": "x", "targets": [], "timestamp": "t"}
    ])
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        res = client.get("/scatola_capriccio/survey", follow_redirects=True)
        assert "権限がありません".encode("utf-8") in res.data
