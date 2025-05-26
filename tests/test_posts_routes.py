import os
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

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
    config.COMMENTS_FILE = os.path.join(_tmpdir.name, "comments.json")

    utils.POINTS_PATH = Path(config.POINTS_FILE)
    utils.POSTS_PATH = Path(config.POSTS_FILE)
    utils.POINTS_HISTORY_PATH = Path(config.POINTS_HISTORY_FILE)
    utils.COMMENTS_PATH = Path(config.COMMENTS_FILE)

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
        tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()
        res = client.get(f"/posts/?start_date={tomorrow}")
        assert b"hello" not in res.data


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


def test_edit_post_route():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        utils.add_post("user1", "news", "orig")
        post_id = utils.load_posts()[0]["id"]
        res = client.post(
            f"/posts/edit/{post_id}",
            data={"category": "news", "text": "updated"},
            follow_redirects=True,
        )
        assert res.status_code == 200
        assert "更新しました".encode("utf-8") in res.data
        assert utils.load_posts()[0]["text"] == "updated"


def test_add_comment_route():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        utils.add_post("user1", "cat", "body")
        post_id = utils.load_posts()[0]["id"]
        res = client.post(
            f"/posts/comment/{post_id}",
            data={"text": "c"},
            follow_redirects=True,
        )
        assert res.status_code == 200
        comments = utils.get_comments(post_id)
        assert comments[0]["text"] == "c"


def test_edit_comment_route():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        utils.add_post("user1", "cat", "body")
        post_id = utils.load_posts()[0]["id"]
        utils.add_comment(post_id, "user1", "before")
        comment_id = utils.load_comments()[0]["id"]
        res = client.post(
            f"/posts/comment/edit/{comment_id}",
            data={"text": "after"},
            follow_redirects=True,
        )
        assert res.status_code == 200
        assert "コメントを更新しました".encode("utf-8") in res.data
        assert utils.get_comments(post_id)[0]["text"] == "after"
