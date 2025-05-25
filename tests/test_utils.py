import json
import os
from datetime import datetime

import app.utils as utils
import config


def setup_function():
    # Prepare a temporary points file
    if os.path.exists(config.POINTS_FILE):
        os.remove(config.POINTS_FILE)
    if os.path.exists(config.POSTS_FILE):
        os.remove(config.POSTS_FILE)
    if os.path.exists(config.POINTS_HISTORY_FILE):
        os.remove(config.POINTS_HISTORY_FILE)
    utils.save_points({"user1": {"A": 1, "O": 0}})


def teardown_function():
    if os.path.exists(config.POINTS_FILE):
        os.remove(config.POINTS_FILE)
    if os.path.exists(config.POSTS_FILE):
        os.remove(config.POSTS_FILE)
    if os.path.exists(config.POINTS_HISTORY_FILE):
        os.remove(config.POINTS_HISTORY_FILE)


def test_login_success():
    user = utils.login("user1", "user1pass")
    assert user is not None
    assert user['username'] == 'user1'
    assert user['role'] == 'user'


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
