from pathlib import Path

import pytest

pytest.importorskip("flask")
pytest.importorskip("flask_wtf")
pytest.importorskip("wtforms")

from app import create_app
import app.utils as utils
import config


@pytest.fixture
def client(tmp_path):
    # Backup original paths
    orig_points = config.POINTS_FILE
    orig_posts = config.POSTS_FILE
    orig_history = config.POINTS_HISTORY_FILE

    # Use temporary directory for data files
    config.POINTS_FILE = str(tmp_path / "points.json")
    config.POSTS_FILE = str(tmp_path / "posts.json")
    config.POINTS_HISTORY_FILE = str(tmp_path / "points_history.json")

    utils.POINTS_PATH = Path(config.POINTS_FILE)
    utils.POSTS_PATH = Path(config.POSTS_FILE)
    utils.POINTS_HISTORY_PATH = Path(config.POINTS_HISTORY_FILE)

    utils.save_points({"user1": {"A": 1, "O": 0}})

    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    with app.test_client() as client:
        yield client

    # Restore original paths
    config.POINTS_FILE = orig_points
    config.POSTS_FILE = orig_posts
    config.POINTS_HISTORY_FILE = orig_history

    utils.POINTS_PATH = Path(config.POINTS_FILE)
    utils.POSTS_PATH = Path(config.POSTS_FILE)
    utils.POINTS_HISTORY_PATH = Path(config.POINTS_HISTORY_FILE)


def login(client, username="admin", password="adminpass"):
    return client.post(
        "/auth/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


def test_login_required_for_dashboard(client):
    resp = client.get("/punto/", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers.get("Location", "")


def test_admin_can_edit_points(client):
    # Login as admin
    login(client)

    # Edit points for user1
    resp = client.post(
        "/punto/edit/user1",
        data={"a": 5, "o": 2, "submit": "保存"},
        follow_redirects=True,
    )
    assert resp.status_code == 200

    points = utils.load_points()
    assert points["user1"] == {"A": 5, "O": 2}
