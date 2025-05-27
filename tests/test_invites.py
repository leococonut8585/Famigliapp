import os
import tempfile
from pathlib import Path

import pytest

flask = pytest.importorskip("flask")

import config
from app import create_app
from app.invites import utils as invite_utils


def setup_module(module):
    global _tmpdir
    _tmpdir = tempfile.TemporaryDirectory()
    config.INVITES_FILE = os.path.join(_tmpdir.name, "invites.json")
    invite_utils.INVITES_PATH = Path(config.INVITES_FILE)


def teardown_module(module):
    _tmpdir.cleanup()


def test_create_and_delete_invite():
    invite_utils.save_invites([])
    code = invite_utils.create_invite()
    invites = invite_utils.load_invites()
    assert invites[0]["code"] == code
    assert invite_utils.delete_invite(code)
    assert invite_utils.load_invites() == []


def test_register_with_invite():
    invite_utils.save_invites([])
    code = invite_utils.create_invite()
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        res = client.post(
            "/auth/register",
            data={"username": "newuser", "password": "pw", "invite": code},
            follow_redirects=True,
        )
        assert res.status_code == 200
        assert "登録しました".encode("utf-8") in res.data
    assert "newuser" in config.USERS
    invites = invite_utils.load_invites()
    assert invites[0]["used_by"] == "newuser"


def test_register_invalid_invite():
    invite_utils.save_invites([])
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        res = client.post(
            "/auth/register",
            data={"username": "bad", "password": "pw", "invite": "wrong"},
            follow_redirects=True,
        )
        assert res.status_code == 200
        assert "招待コードが無効です".encode("utf-8") in res.data
    assert "bad" not in config.USERS
