import config
from app import create_app, utils
import pytest
import tempfile
from pathlib import Path
import io

flask = pytest.importorskip("flask")


def setup_module(module):
    global _tmpdir
    _tmpdir = tempfile.TemporaryDirectory()
    config.POINTS_FILE = Path(_tmpdir.name) / "points.json"
    config.POSTS_FILE = Path(_tmpdir.name) / "posts.json"
    config.POINTS_HISTORY_FILE = Path(_tmpdir.name) / "points_history.json"

    utils.POINTS_PATH = Path(config.POINTS_FILE)
    utils.POSTS_PATH = Path(config.POSTS_FILE)
    utils.POINTS_HISTORY_PATH = Path(config.POINTS_HISTORY_FILE)

    utils.save_points({"admin": {"A": 0, "O": 0}})


def teardown_module(module):
    _tmpdir.cleanup()


def test_add_and_list_bravissimo():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "a@example.com"}
        res = client.post("/bravissimo/add", data={"text": "good"}, follow_redirects=True)
        assert res.status_code == 200
        assert b"good" in res.data
        # ensure list page shows the post
        res = client.get("/bravissimo/")
        assert b"good" in res.data


def test_add_requires_admin():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        res = client.post("/bravissimo/add", data={"text": "hello"}, follow_redirects=True)
        assert "権限がありません".encode("utf-8") in res.data


def test_add_with_audio(tmp_path):
    app = create_app()
    app.config["TESTING"] = True
    audio_path = tmp_path / "test.wav"
    audio_path.write_bytes(b"dummy")
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "a@example.com"}
        with open(audio_path, "rb") as f:
            res = client.post(
                "/bravissimo/add",
                data={"text": "bravo", "audio": (f, "test.wav")},
                content_type="multipart/form-data",
                follow_redirects=True,
            )
        assert res.status_code == 200
        assert b"bravo" in res.data
        assert b"<audio" in res.data
    assert Path("static/uploads/test.wav").exists()


def test_filter_by_target():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "a@example.com"}
        client.post("/bravissimo/add", data={"text": "nice", "target": "user1"}, follow_redirects=True)
        res = client.get("/bravissimo/?target=user1")
        assert b"nice" in res.data
        res = client.get("/bravissimo/?target=user2")
        assert b"nice" not in res.data


def test_reject_invalid_extension():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "a@example.com"}
        data = {"text": "x", "audio": (io.BytesIO(b"x"), "bad.exe")}
        res = client.post("/bravissimo/add", data=data, follow_redirects=True)
        assert "許可されていないファイル形式です".encode("utf-8") in res.data
        assert utils.load_posts() == []


def test_reject_large_file():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "a@example.com"}
        big = io.BytesIO(b"x" * (10 * 1024 * 1024 + 1))
        data = {"text": "x", "audio": (big, "big.wav")}
        res = client.post("/bravissimo/add", data=data, follow_redirects=True)
        assert "ファイルサイズが大きすぎます".encode("utf-8") in res.data
        assert utils.load_posts() == []
