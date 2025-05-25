import json
import os

import app.utils as utils
import config


def setup_function():
    # Prepare a temporary points file
    if os.path.exists(config.POINTS_FILE):
        os.remove(config.POINTS_FILE)
    if os.path.exists(config.POSTS_FILE):
        os.remove(config.POSTS_FILE)
    utils.save_points({"user1": {"A": 1, "O": 0}})


def teardown_function():
    if os.path.exists(config.POINTS_FILE):
        os.remove(config.POINTS_FILE)
    if os.path.exists(config.POSTS_FILE):
        os.remove(config.POSTS_FILE)


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
