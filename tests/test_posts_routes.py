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
    config.POSTS_FILE = os.path.join(_tmpdir.name, "posts.json")
    config.POINTS_HISTORY_FILE = os.path.join(_tmpdir.name, "points_history.json")

    utils.POINTS_PATH = Path(config.POINTS_FILE)
    utils.POSTS_PATH = Path(config.POSTS_FILE)
    utils.POINTS_HISTORY_PATH = Path(config.POINTS_HISTORY_FILE)

    utils.save_points({"user1": {"A": 0, "O": 0}})


def teardown_module(module):
    _tmpdir.cleanup()


def test_add_and_list_post():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        res = client.post("/posts/add", data={"category": "news", "text": "hello"}, follow_redirects=True)
        assert res.status_code == 200
        assert b"hello" in res.data


def test_delete_post_route():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "admin@example.com"}
        utils.add_post("admin", "news", "bye")
        post_id = utils.load_posts()[0]["id"]
        res = client.get(f"/posts/delete/{post_id}", follow_redirects=True)
        assert res.status_code == 200
        assert utils.load_posts() == []
