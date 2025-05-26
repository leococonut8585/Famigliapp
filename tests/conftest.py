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
