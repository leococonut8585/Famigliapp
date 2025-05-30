import os
import tempfile
from pathlib import Path
from datetime import datetime

import config
from app import create_app, utils
import pytest

flask = pytest.importorskip("flask")


def setup_module(module):
    global _tmpdir
    _tmpdir = tempfile.TemporaryDirectory()
    config.POINTS_FILE = os.path.join(_tmpdir.name, "points.json")
    config.POINTS_HISTORY_FILE = os.path.join(_tmpdir.name, "points_history.json")
    config.POSTS_FILE = os.path.join(_tmpdir.name, "posts.json")
    config.POINTS_CONSUMPTION_FILE = os.path.join(_tmpdir.name, "points_consumption.json")

    utils.POINTS_PATH = Path(config.POINTS_FILE)
    utils.POINTS_HISTORY_PATH = Path(config.POINTS_HISTORY_FILE)
    utils.POSTS_PATH = Path(config.POSTS_FILE)
    utils.POINTS_CONSUMPTION_PATH = Path(config.POINTS_CONSUMPTION_FILE)

    utils.save_points({"u1": {"A": 5, "O": 1}, "u2": {"A": 3, "O": 0}})


def teardown_module(module):
    _tmpdir.cleanup()


def test_rankings_route():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "admin@example.com"}
        res = client.get("/punto/rankings?metric=A&period=all")
        assert res.status_code == 200
        assert b"u1" in res.data
        assert b"u2" in res.data


def test_edit_form_displays_u_points():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "admin@example.com"}
        res = client.get("/punto/edit/u1")
        assert res.status_code == 200
        assert "Uポイント".encode("utf-8") in res.data


def test_history_route():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "admin@example.com"}
        utils.add_points_consumption("u1", "aaa")
        res = client.get("/punto/history")
        assert res.status_code == 200
        assert "ポイント消費履歴".encode("utf-8") in res.data


def test_export_history_csv(tmp_path):
    app = create_app()
    app.config["TESTING"] = True
    utils.add_points_consumption("u1", "b")
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "u1", "role": "user", "email": "u1@example.com"}
        res = client.get("/punto/history/export", follow_redirects=True)
        assert res.status_code == 200
        assert "権限がありません".encode("utf-8") in res.data
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "admin@example.com"}
        res = client.get("/punto/history/export")
        assert res.status_code == 200
        assert res.headers["Content-Type"].startswith("text/csv")
        assert b"timestamp" in res.data


def test_graph_route():
    app = create_app()
    app.config["TESTING"] = True
    ts = datetime(2021, 6, 1, 10, 0, 0)
    utils.log_points_change("u1", 1, 0, ts)
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "admin@example.com"}
        res = client.post(
            "/punto/graph",
            data={"start": "2021-06-01", "end": "2021-06-02"},
        )
        assert res.status_code == 200
        assert b"pointsChart" in res.data
        assert b"2021-06-01" in res.data
