USERS = {
    "admin": {"password": "adminpass", "role": "admin", "email": "admin@example.com"},
    "user1": {"password": "user1pass", "role": "user", "email": "user1@example.com"},
    "user2": {"password": "user2pass", "role": "user", "email": "user2@example.com"},
}

POINTS_FILE = "points.json"
POINTS_HISTORY_FILE = "points_history.json"
POSTS_FILE = "posts.json"
SECRET_KEY = "replace-this-with-a-random-secret"

# Default database location for SQLAlchemy-based models
SQLALCHEMY_DATABASE_URI = "sqlite:///famigliapp.db"
SQLALCHEMY_TRACK_MODIFICATIONS = False
