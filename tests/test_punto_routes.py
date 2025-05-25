import os
import tempfile
from pathlib import Path

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

    utils.POINTS_PATH = Path(config.POINTS_FILE)
    utils.POINTS_HISTORY_PATH = Path(config.POINTS_HISTORY_FILE)
    utils.POSTS_PATH = Path(config.POSTS_FILE)

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
