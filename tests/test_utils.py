import os
import tempfile
from pathlib import Path
from datetime import datetime

import app.utils as utils
import config

_temp_dir = None
_original_points_file = config.POINTS_FILE
_original_posts_file = config.POSTS_FILE
_original_history_file = config.POINTS_HISTORY_FILE


def setup_function():
    """Create a temporary directory for JSON files used in tests."""
    global _temp_dir
    _temp_dir = tempfile.TemporaryDirectory()

    config.POINTS_FILE = os.path.join(_temp_dir.name, "points.json")
    config.POSTS_FILE = os.path.join(_temp_dir.name, "posts.json")
    config.POINTS_HISTORY_FILE = os.path.join(_temp_dir.name, "points_history.json")

    utils.POINTS_PATH = Path(config.POINTS_FILE)
    utils.POSTS_PATH = Path(config.POSTS_FILE)
    utils.POINTS_HISTORY_PATH = Path(config.POINTS_HISTORY_FILE)

    utils.save_points({"user1": {"A": 1, "O": 0}})


def teardown_function():
    """Cleanup the temporary directory and restore config paths."""
    global _temp_dir

    if _temp_dir:
        _temp_dir.cleanup()
        assert not os.path.exists(config.POINTS_FILE)
        assert not os.path.exists(config.POSTS_FILE)
        assert not os.path.exists(config.POINTS_HISTORY_FILE)
        _temp_dir = None

    config.POINTS_FILE = _original_points_file
    config.POSTS_FILE = _original_posts_file
    config.POINTS_HISTORY_FILE = _original_history_file

    utils.POINTS_PATH = Path(config.POINTS_FILE)
    utils.POSTS_PATH = Path(config.POSTS_FILE)
    utils.POINTS_HISTORY_PATH = Path(config.POINTS_HISTORY_FILE)


def test_login_success():
    user = utils.login("user1", "user1pass")
    assert user is not None
    assert user["username"] == "user1"
    assert user["role"] == "user"


def test_login_failure():
    assert utils.login("user1", "wrong") is None


def test_edit_points():
    points = utils.load_points()
    assert points["user1"] == {"A": 1, "O": 0}
    points["user1"]["A"] = 5
    points["user1"]["O"] = 2
    utils.save_points(points)
    saved = utils.load_points()
    assert saved["user1"] == {"A": 5, "O": 2}


def test_add_post_and_delete():
    utils.add_post("user1", "bravissimo", "hello")
    posts = utils.load_posts()
    assert len(posts) == 1
    assert posts[0]["author"] == "user1"
    assert posts[0]["category"] == "bravissimo"
    assert posts[0]["text"] == "hello"
    assert utils.delete_post(posts[0]["id"])
    assert utils.load_posts() == []


def test_post_id_increment_after_middle_delete():
    utils.add_post("u1", "bravissimo", "one")
    utils.add_post("u2", "bravissimo", "two")
    posts = utils.load_posts()
    first_id = posts[0]["id"]
    second_id = posts[1]["id"]
    assert utils.delete_post(first_id)
    utils.add_post("u3", "bravissimo", "three")
    ids = [p["id"] for p in utils.load_posts()]
    assert ids == [second_id, second_id + 1]


def test_get_ranking():
    utils.save_points({"u1": {"A": 5, "O": 1}, "u2": {"A": 3, "O": 0}})
    ranking_a = utils.get_ranking("A")
    assert ranking_a[0] == ("u1", 5)
    ranking_u = utils.get_ranking("U")
    assert ranking_u[0] == ("u1", 4)


def test_get_ranking_with_period():
    ts1 = datetime(2021, 1, 1, 10, 0, 0)
    ts2 = datetime(2021, 1, 2, 10, 0, 0)
    ts3 = datetime(2021, 1, 8, 10, 0, 0)
    utils.log_points_change("u1", 5, 0, ts1)
    utils.log_points_change("u2", 3, 0, ts2)
    utils.log_points_change("u1", 2, 0, ts3)
    start = datetime(2021, 1, 1)
    end = datetime(2021, 1, 7)
    ranking = utils.get_ranking("A", start=start, end=end)
    assert ranking[0] == ("u1", 5)
    assert ranking[1] == ("u2", 3)


def test_get_ranking_monthly_and_yearly():
    now = datetime(2021, 2, 15, 0, 0, 0)
    ts_prev_year = datetime(2020, 12, 31, 10, 0, 0)
    ts_last_month = datetime(2021, 1, 20, 10, 0, 0)
    ts_current_month = datetime(2021, 2, 5, 10, 0, 0)
    utils.log_points_change("u1", 5, 0, ts_prev_year)
    utils.log_points_change("u2", 2, 0, ts_last_month)
    utils.log_points_change("u3", 3, 0, ts_current_month)
    ranking_month = utils.get_ranking("A", period="monthly", end=now)
    assert ranking_month == [("u3", 3)]
    ranking_year = utils.get_ranking("A", period="yearly", end=now)
    assert ranking_year == [("u3", 3), ("u2", 2)]


def test_filter_posts():
    utils.add_post("u1", "bravissimo", "hello world")
    utils.add_post("u2", "bravissimo", "goodbye world")
    utils.add_post("u1", "corso", "hello again")

    assert len(utils.filter_posts(category="bravissimo")) == 2
    assert len(utils.filter_posts(author="u1")) == 2
    kw = utils.filter_posts(keyword="goodbye")
    assert len(kw) == 1 and kw[0]["author"] == "u2"
    combo = utils.filter_posts(category="bravissimo", author="u2")
    assert len(combo) == 1 and combo[0]["author"] == "u2"


def test_update_post():
    utils.add_post("u1", "news", "old")
    post_id = utils.load_posts()[0]["id"]
    assert utils.update_post(post_id, "news", "new text")
    posts = utils.load_posts()
    assert posts[0]["text"] == "new text"


def test_load_points_history_after_logging():
    ts = datetime(2021, 3, 1, 12, 0, 0)
    utils.log_points_change("u1", 2, -1, ts)
    utils.log_points_change("u2", -3, 0, ts)
    history = utils.load_points_history()
    assert history[-2:] == [
        {
            "username": "u1",
            "A": 2,
            "O": -1,
            "timestamp": ts.isoformat(timespec="seconds"),
        },
        {
            "username": "u2",
            "A": -3,
            "O": 0,
            "timestamp": ts.isoformat(timespec="seconds"),
        },
    ]


def test_filter_points_history():
    ts1 = datetime(2021, 4, 1, 12, 0, 0)
    ts2 = datetime(2021, 4, 5, 12, 0, 0)
    utils.log_points_change("u1", 1, 0, ts1)
    utils.log_points_change("u2", 2, 0, ts2)

    start = datetime(2021, 4, 3)
    end = datetime(2021, 4, 6)
    results = utils.filter_points_history(start=start, end=end, username="u2")

    assert len(results) == 1
    assert results[0]["username"] == "u2"
    assert results[0]["timestamp"] == ts2.isoformat(timespec="seconds")


def test_export_history_csv(tmp_path):
    ts = datetime(2021, 5, 1, 8, 0, 0)
    utils.log_points_change("u1", 1, 0, ts)
    csv_path = tmp_path / "hist.csv"
    utils.export_points_history_csv(str(csv_path))
    with open(csv_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines()]
    assert lines[0] == "timestamp,username,A,O"
    assert lines[1].startswith(ts.isoformat(timespec="seconds") + ",u1,1,0")
