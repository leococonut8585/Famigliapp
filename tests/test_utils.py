import json
import os

import app.utils as utils
import config


def setup_function():
    # Prepare a temporary points file
    if os.path.exists(config.POINTS_FILE):
        os.remove(config.POINTS_FILE)
    utils.save_points({"user1": {"A": 1, "O": 0}})


def teardown_function():
    if os.path.exists(config.POINTS_FILE):
        os.remove(config.POINTS_FILE)


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
