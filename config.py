USERS = {
    "admin": {"password": "adminpass", "role": "admin", "email": "admin@example.com"},
    "leo": {"password": "leococonut85", "role": "admin", "email": "leo@example.com"},
    "lady": {"password": "shihopoteto850", "role": "admin", "email": "lady@example.com"},
    "raito": {"password": "raitocetriolo851", "role": "user", "email": "raito@example.com"},
    "hitomi": {"password": "hitomioniku852", "role": "user", "email": "hitomi@example.com"},
    "sara": {"password": "sarapasta853", "role": "user", "email": "sara@example.com"},
    "jun": {"password": "giunamazake854", "role": "user", "email": "jun@example.com"},
    "nanchan": {"password": "shojigruto855", "role": "user", "email": "nanchan@example.com"},
    "hachi": {"password": "hachipakuchi856", "role": "user", "email": "hachi@example.com"},
    "kie": {"password": "kieriso857", "role": "user", "email": "kie@example.com"},
    "gumi": {"password": "kumigumi858", "role": "user", "email": "gumi@example.com"},
}

# Users that should not appear in selection lists
EXCLUDED_USERS = {"admin"}

POINTS_FILE = "points.json"
POINTS_HISTORY_FILE = "points_history.json"
POINTS_CONSUMPTION_FILE = "points_consumption.json"
POSTS_FILE = "posts.json"
COMMENTS_FILE = "comments.json"
INTRATTENIMENTO_FILE = "intrattenimento.json"
INTRATTENIMENTO_TASK_FILE = "intrattenimento_tasks.json"
CORSO_FILE = "corso.json"
SCATOLA_FILE = "scatola_capriccio.json"
SCATOLA_SURVEY_FILE = "scatola_surveys.json"
QUEST_BOX_FILE = "quests.json"
NEDARI_FILE = "nedari.json"
VOTE_BOX_FILE = "votebox.json"
CALENDAR_FILE = "events.json"
CALENDAR_RULES_FILE = "calendar_rules.json"
RESOCONTO_FILE = "resoconto.json"
SEMINARIO_FILE = "seminario.json"
PRINCIPESSINA_FILE = "principessina.json"
PRINCIPESSINA_MEDIA_FILE = "principessina_media.json"
PRINCIPESSINA_REPORT_FOLDERS_FILE = "principessina_report_folders.json"
MONSIGNORE_FILE = "monsignore.json"
MONSIGNORE_KADAI_FILE = "monsignore_kadai.json"
INVITES_FILE = "invites.json"
SECRET_KEY = "replace-this-with-a-random-secret"
SQLALCHEMY_DATABASE_URI = "sqlite:///famigliapp.db"
SQLALCHEMY_TRACK_MODIFICATIONS = False

MAIL_SERVER = "localhost"
MAIL_PORT = 25
MAIL_SENDER = "famigliapp@example.com"
LINE_NOTIFY_TOKEN = ""
PUSHBULLET_TOKEN = ""
MAIL_ENABLED = False
