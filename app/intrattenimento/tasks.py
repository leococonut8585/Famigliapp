from datetime import date, datetime
from typing import List

import config
from app.utils import send_email
from . import utils


def notify_missing_posts(today: date = date.today()) -> List[str]:
    """Send reminder emails if a user hasn't posted to intrattenimento today."""
    posts = utils.load_posts()
    authors_with_post = set()
    for p in posts:
        ts = p.get("timestamp")
        try:
            ts_dt = datetime.fromisoformat(ts)
        except Exception:
            continue
        if ts_dt.date() == today:
            authors_with_post.add(p.get("author"))

    notified: List[str] = []
    for username, info in config.USERS.items():
        if username in authors_with_post:
            continue
        email = info.get("email")
        if email:
            send_email(
                "Intrattenimento reminder",
                "Please submit today's entertainment feedback",
                email,
            )
            notified.append(username)
    return notified
