from pathlib import Path
import os
import tempfile
import io

import config
import pytest

flask = pytest.importorskip("flask")

from app import create_app
from app.principessina import utils


def setup_module(module):
    global _tmpdir
    _tmpdir = tempfile.TemporaryDirectory()
    config.PRINCIPESSINA_FILE = os.path.join(_tmpdir.name, "principessina.json")
    utils.PRINCIPESSINA_PATH = Path(config.PRINCIPESSINA_FILE)


def teardown_module(module):
    _tmpdir.cleanup()


def test_add_and_list():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        res = client.post(
            "/principessina/add",
            data={"body": "b"},
            follow_redirects=True,
        )
        assert res.status_code == 200
        assert "投稿しました".encode("utf-8") in res.data
        res = client.get("/principessina/")
        assert b"b" in res.data


def test_delete_route():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "a@example.com"}
        utils.add_post("admin", "body")
        post_id = utils.load_posts()[0]["id"]
        res = client.get(f"/principessina/delete/{post_id}", follow_redirects=True)
        assert res.status_code == 200
        assert utils.load_posts() == []


def test_download_route(tmp_path):
    app = create_app()
    app.config["TESTING"] = True
    os.makedirs(os.path.join("static", "uploads"), exist_ok=True)
    filepath = os.path.join("static", "uploads", "file.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("x")
    utils.add_post("user1", "body", "file.txt")
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        res = client.get("/principessina/download/file.txt")
        assert res.status_code == 200


def test_filter_posts_case_insensitive():
    utils.save_posts([])
    utils.add_post("admin", "Hello")
    res = utils.filter_posts(keyword="hello")
    assert len(res) == 1
    assert res[0]["body"] == "Hello"


def test_reject_invalid_extension():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        data = {"body": "b", "attachment": (io.BytesIO(b"x"), "bad.exe")}
        res = client.post("/principessina/add", data=data, follow_redirects=True)
        assert "許可されていないファイル形式です".encode("utf-8") in res.data
        assert utils.load_posts() == []


def test_reject_large_file():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        big = io.BytesIO(b"x" * (10 * 1024 * 1024 + 1))
        data = {"body": "b", "attachment": (big, "big.txt")}
        res = client.post("/principessina/add", data=data, follow_redirects=True)
        assert "ファイルサイズが大きすぎます".encode("utf-8") in res.data
        assert utils.load_posts() == []

