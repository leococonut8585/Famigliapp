import os
import tempfile
from pathlib import Path
from datetime import date

import config
import pytest

flask = pytest.importorskip("flask")

from app import create_app
from app.resoconto import utils


def setup_module(module):
    global _tmpdir
    _tmpdir = tempfile.TemporaryDirectory()
    config.RESOCONTO_FILE = os.path.join(_tmpdir.name, "resoconto.json")
    utils.REPORTS_PATH = Path(config.RESOCONTO_FILE)


def teardown_module(module):
    _tmpdir.cleanup()


def test_add_and_list_report():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        res = client.post(
            "/resoconto/add",
            data={"date": "2025-01-01", "body": "work"},
            follow_redirects=True,
        )
        assert res.status_code == 200
        assert "投稿しました".encode("utf-8") in res.data
        res = client.get("/resoconto/")
        assert "work".encode("utf-8") in res.data


def test_delete_report_as_admin():
    app = create_app()
    app.config["TESTING"] = True
    utils.add_report("user1", date.fromisoformat("2025-02-01"), "del")
    report_id = utils.load_reports()[0]["id"]
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "a@example.com"}
        res = client.get(f"/resoconto/delete/{report_id}", follow_redirects=True)
        assert res.status_code == 200
        assert utils.load_reports() == []
