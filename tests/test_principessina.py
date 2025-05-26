from pathlib import Path
import os
import tempfile

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

