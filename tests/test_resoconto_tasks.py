import os
import tempfile
from pathlib import Path

import config
from app import utils
from datetime import date
import pytest

flask = pytest.importorskip("flask")
from app.resoconto import utils as res_utils
from app.resoconto import tasks


def setup_module(module):
    global _tmpdir
    _tmpdir = tempfile.TemporaryDirectory()
    config.POSTS_FILE = os.path.join(_tmpdir.name, "posts.json")
    utils.POSTS_PATH = Path(config.POSTS_FILE)
    config.RESOCONTO_FILE = os.path.join(_tmpdir.name, "resoconto.json")
    res_utils.REPORTS_PATH = Path(config.RESOCONTO_FILE)


def teardown_module(module):
    _tmpdir.cleanup()


def test_daily_post_job(monkeypatch):
    utils.add_post("u1", "news", "a")
    utils.add_post("u2", "news", "b")
    utils.add_post("u1", "other", "c")

    sent = {}

    def dummy_send(subject, body, to):
        sent["subject"] = subject
        sent["body"] = body
        sent["to"] = to

    monkeypatch.setattr(tasks, "send_email", dummy_send)

    result = tasks.daily_post_job()

    assert result["ranking"][0] == ("u1", 2)
    assert result["ranking"][1] == ("u2", 1)
    assert result["summary"]["top_category"] == "news"
    assert result["summary"]["total_posts"] == 3
    assert sent["to"] == config.USERS.get("admin", {}).get("email")


def test_daily_report_job(monkeypatch):
    res_utils.add_report("u1", date.fromisoformat("2025-01-01"), "short")
    res_utils.add_report("u2", date.fromisoformat("2025-01-01"), "word " * 30)

    sent = {}

    def dummy_send(subject, body, to):
        sent["to"] = to
        sent["body"] = body

    monkeypatch.setattr(tasks, "send_email", dummy_send)

    result = tasks.daily_report_job()

    assert result["ranking"][0][0] == "u2"
    assert sent["to"] == config.USERS.get("admin", {}).get("email")
