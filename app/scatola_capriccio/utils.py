import json
from pathlib import Path
from datetime import datetime

import config
from app.utils import send_email

SCATOLA_PATH = Path(getattr(config, "SCATOLA_FILE", "scatola_capriccio.json"))
SURVEYS_PATH = Path(getattr(config, "SCATOLA_SURVEY_FILE", "scatola_surveys.json"))


def load_posts():
    if SCATOLA_PATH.exists():
        with open(SCATOLA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_posts(posts):
    with open(SCATOLA_PATH, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)


def add_post(author, body):
    posts = load_posts()
    next_id = max((p.get("id", 0) for p in posts), default=0) + 1
    posts.append({
        "id": next_id,
        "author": author,
        "body": body,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    })
    save_posts(posts)


def load_surveys():
    if SURVEYS_PATH.exists():
        with open(SURVEYS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_surveys(surveys):
    with open(SURVEYS_PATH, "w", encoding="utf-8") as f:
        json.dump(surveys, f, ensure_ascii=False, indent=2)


def add_survey(author: str, question: str, targets: list) -> None:
    surveys = load_surveys()
    next_id = max((s.get("id", 0) for s in surveys), default=0) + 1
    surveys.append(
        {
            "id": next_id,
            "author": author,
            "question": question,
            "targets": targets,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
    )
    save_surveys(surveys)

    for t in targets:
        info = config.USERS.get(t)
        if info and info.get("email"):
            send_email("Survey", question, info["email"])
