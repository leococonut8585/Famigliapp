import os
import tempfile
from pathlib import Path

import config
import pytest

flask = pytest.importorskip("flask")

from app import create_app
from app.monsignore import utils


def setup_module(module):
    global _tmpdir
    _tmpdir = tempfile.TemporaryDirectory()
    config.MONSIGNORE_FILE = os.path.join(_tmpdir.name, "monsignore.json")
    utils.MONSIGNORE_PATH = Path(config.MONSIGNORE_FILE)


def teardown_module(module):
    _tmpdir.cleanup()


def test_add_list_and_delete(tmp_path):
    app = create_app()
    app.config["TESTING"] = True
    img = tmp_path / "img.png"
    img.write_bytes(b"dummy")
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        with open(img, "rb") as f:
            res = client.post(
                "/monsignore/add",
                data={"body": "hello", "image": (f, "img.png")},
                content_type="multipart/form-data",
                follow_redirects=True,
            )
        assert res.status_code == 200
        assert "投稿しました".encode("utf-8") in res.data
        res = client.get("/monsignore/")
        assert b"hello" in res.data
        assert b"<img" in res.data
        post_id = utils.load_posts()[0]["id"]
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "a@example.com"}
        res = client.get(f"/monsignore/delete/{post_id}", follow_redirects=True)
        assert res.status_code == 200
        assert utils.load_posts() == []


def test_filter_posts_case_insensitive():
    utils.save_posts([])
    utils.add_post("admin", "Hello")
    res = utils.filter_posts(keyword="hello")
    assert len(res) == 1
    assert res[0]["body"] == "Hello"


def test_add_sends_notifications(monkeypatch, tmp_path):
    app = create_app()
    app.config["TESTING"] = True
    img = tmp_path / "img.png"
    img.write_bytes(b"dummy")
    sent = []

    from app.monsignore import routes as mon_routes

    def dummy_send(subject, body, to):
        sent.append(to)

    monkeypatch.setattr(mon_routes, "send_email", dummy_send)

    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        with open(img, "rb") as f:
            client.post(
                "/monsignore/add",
                data={"body": "hello", "image": (f, "img.png")},
                content_type="multipart/form-data",
                follow_redirects=True,
            )

    expected = {u["email"] for u in config.USERS.values()}
    assert set(sent) == expected
