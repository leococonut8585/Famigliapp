import pytest

flask = pytest.importorskip("flask")

import config
import tempfile
from pathlib import Path
from app import create_app
from app.scatola_capriccio import utils


def setup_module(module):
    global _tmpdir
    _tmpdir = tempfile.TemporaryDirectory()
    config.SCATOLA_FILE = str(Path(_tmpdir.name) / "scatola.json")
    utils.SCATOLA_PATH = Path(config.SCATOLA_FILE)


def teardown_module(module):
    _tmpdir.cleanup()


def test_add_and_admin_list():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        res = client.post("/scatola_capriccio/add", data={"body": "hello"}, follow_redirects=True)
        assert res.status_code == 200
        assert "投稿しました".encode("utf-8") in res.data
        assert utils.load_posts()[0]["body"] == "hello"
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "a@example.com"}
        res = client.get("/scatola_capriccio/")
        assert b"hello" in res.data


def test_non_admin_cannot_view():
    app = create_app()
    app.config["TESTING"] = True
    utils.add_post("user1", "feedback")
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        res = client.get("/scatola_capriccio/", follow_redirects=True)
        assert "権限がありません".encode("utf-8") in res.data
