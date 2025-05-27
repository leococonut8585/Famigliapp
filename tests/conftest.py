import pytest
import config

@pytest.fixture
def test_user():
    username = "testuser"
    config.USERS[username] = {
        "password": "testpass",
        "role": "user",
        "email": "test@example.com",
    }
    yield {"username": username, "password": "testpass"}
    config.USERS.pop(username, None)


@pytest.fixture(autouse=True)
def ensure_default_users():
    added = []
    if "user1" not in config.USERS:
        config.USERS["user1"] = {"password": "user1pass", "role": "user", "email": "u1@example.com"}
        added.append("user1")
    if "user2" not in config.USERS:
        config.USERS["user2"] = {"password": "user2pass", "role": "user", "email": "u2@example.com"}
        added.append("user2")
    yield
    for u in added:
        config.USERS.pop(u, None)
