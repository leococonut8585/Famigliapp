USERS = {
    "admin": {"password": "adminpass", "role": "admin", "email": "admin@example.com"},
    "user1": {"password": "user1pass", "role": "user", "email": "user1@example.com"},
    "user2": {"password": "user2pass", "role": "user", "email": "user2@example.com"},
}

POINTS_FILE = "points.json"
POINTS_HISTORY_FILE = "points_history.json"
POSTS_FILE = "posts.json"
INTRATTENIMENTO_FILE = "intrattenimento.json"
CORSO_FILE = "corso.json"
SCATOLA_FILE = "scatola_capriccio.json"
QUEST_BOX_FILE = "quests.json"
CALENDAR_FILE = "events.json"
RESOCONTO_FILE = "resoconto.json"
LEZZIONE_FILE = "lezzione.json"
PRINCIPESSINA_FILE = "principessina.json"
MONSIGNORE_FILE = "monsignore.json"
SECRET_KEY = "replace-this-with-a-random-secret"
SQLALCHEMY_DATABASE_URI = "sqlite:///famigliapp.db"
SQLALCHEMY_TRACK_MODIFICATIONS = False

MAIL_SERVER = "localhost"
MAIL_PORT = 25
MAIL_SENDER = "famigliapp@example.com"
