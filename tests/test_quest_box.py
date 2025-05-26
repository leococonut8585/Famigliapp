import os
import tempfile
from pathlib import Path

import pytest

flask = pytest.importorskip("flask")

import config
from app import create_app
from app.quest_box import utils


def setup_module(module):
    global _tmpdir
    _tmpdir = tempfile.TemporaryDirectory()
    config.QUEST_BOX_FILE = os.path.join(_tmpdir.name, "quests.json")
    utils.QUESTS_PATH = Path(config.QUEST_BOX_FILE)


def teardown_module(module):
    _tmpdir.cleanup()


def test_add_and_list_quest():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        res = client.post(
            "/quest_box/add",
            data={"title": "t", "body": "b", "due_date": "2030-01-01"},
            follow_redirects=True,
        )
        assert res.status_code == 200
        assert "投稿しました".encode("utf-8") in res.data
        res = client.get("/quest_box/")
        assert b"t" in res.data
        assert b"2030-01-01" in res.data


def test_accept_and_complete():
    app = create_app()
    app.config["TESTING"] = True
    utils.add_quest("user1", "q", "b", None)
    quest_id = utils.load_quests()[0]["id"]
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user2", "role": "user", "email": "u2@example.com"}
        res = client.get(f"/quest_box/accept/{quest_id}", follow_redirects=True)
        assert res.status_code == 200
        assert utils.load_quests()[0]["status"] == "accepted"
        res = client.get(f"/quest_box/complete/{quest_id}", follow_redirects=True)
        assert res.status_code == 200
        assert utils.load_quests()[0]["status"] == "completed"


def test_delete_route():
    app = create_app()
    app.config["TESTING"] = True
    utils.add_quest("user1", "x", "y", None)
    quest_id = utils.load_quests()[0]["id"]
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "a@example.com"}
        res = client.get(f"/quest_box/delete/{quest_id}", follow_redirects=True)
        assert res.status_code == 200
        assert utils.load_quests() == []


def test_reward_route():
    app = create_app()
    app.config["TESTING"] = True
    utils.add_quest("user1", "r", "b", None)
    quest_id = utils.load_quests()[0]["id"]
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "admin", "role": "admin", "email": "a@example.com"}
        res = client.post(
            f"/quest_box/reward/{quest_id}",
            data={"reward": "100"},
            follow_redirects=True,
        )
        assert res.status_code == 200
        assert utils.load_quests()[0]["reward"] == "100"


def test_add_with_assigned_to():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = {"username": "user1", "role": "user", "email": "u1@example.com"}
        res = client.post(
            "/quest_box/add",
            data={"title": "t2", "body": "b2", "assigned_to": "user2"},
            follow_redirects=True,
        )
        assert res.status_code == 200
        quests = utils.load_quests()
        assert quests[0]["assigned_to"] == "user2"
        res = client.get("/quest_box/")
        assert b"user2" in res.data

