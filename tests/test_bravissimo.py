import config
from app import create_app, utils
import pytest
import tempfile
from pathlib import Path
import io
import wave

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


def _create_wav(path: Path, seconds: int = 1):
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(1)
        wf.setframerate(1)
        wf.writeframes(b"\0" * seconds)


def test_add_and_list_bravissimo(tmp_path):
    app = create_app()
    app.config["TESTING"] = True
    audio_path = tmp_path / "t.wav"
    _create_wav(audio_path, 5)
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "a@example.com"}
        with open(audio_path, "rb") as f:
            res = client.post(
                "/bravissimo/add",
                data={"target": "raito", "audio": (f, "t.wav")},
                content_type="multipart/form-data",
                follow_redirects=True,
            )
        assert res.status_code == 200
        assert b"<audio" in res.data
        res = client.get("/bravissimo/")
        assert b"<audio" in res.data


def test_add_requires_admin(tmp_path):
    app = create_app()
    app.config["TESTING"] = True
    audio_path = tmp_path / "a.wav"
    _create_wav(audio_path)
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        with open(audio_path, "rb") as f:
            res = client.post(
                "/bravissimo/add",
                data={"target": "raito", "audio": (f, "a.wav")},
                content_type="multipart/form-data",
                follow_redirects=True,
            )
        assert "権限がありません".encode("utf-8") in res.data


def test_add_with_audio(tmp_path):
    app = create_app()
    app.config["TESTING"] = True
    audio_path = tmp_path / "test.wav"
    _create_wav(audio_path)
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "a@example.com"}
        with open(audio_path, "rb") as f:
            res = client.post(
                "/bravissimo/add",
                data={"target": "raito", "audio": (f, "test.wav")},
                content_type="multipart/form-data",
                follow_redirects=True,
            )
        assert res.status_code == 200
        assert b"<audio" in res.data
    assert Path("static/uploads/test.wav").exists()


def test_filter_by_target():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "a@example.com"}
        audio = io.BytesIO(b"a" * 4)
        client.post(
            "/bravissimo/add",
            data={"target": "raito", "audio": (audio, "n.wav")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        res = client.get("/bravissimo/user/raito")
        assert b"<audio" in res.data
        res = client.get("/bravissimo/user/hitomi")
        assert b"<audio" not in res.data


def test_reject_invalid_extension():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "a@example.com"}
        data = {"target": "raito", "audio": (io.BytesIO(b"x"), "bad.exe")}
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
        data = {"target": "raito", "audio": (big, "big.wav")}
        res = client.post("/bravissimo/add", data=data, follow_redirects=True)
        assert "ファイルサイズが大きすぎます".encode("utf-8") in res.data
        assert utils.load_posts() == []


def test_reject_long_audio(tmp_path):
    app = create_app()
    app.config["TESTING"] = True
    long_audio = tmp_path / "long.wav"
    _create_wav(long_audio, 1201)
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "a@example.com"}
        with open(long_audio, "rb") as f:
            data = {"target": "raito", "audio": (f, "long.wav")}
            res = client.post("/bravissimo/add", data=data, content_type="multipart/form-data", follow_redirects=True)
        assert "20分を超える音声はアップロードできません".encode("utf-8") in res.data
        assert utils.load_posts() == []
