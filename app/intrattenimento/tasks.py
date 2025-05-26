from datetime import date, datetime
from typing import List

try:  # pragma: no cover - optional dependency
    from apscheduler.schedulers.background import BackgroundScheduler
except Exception:  # pragma: no cover - optional dependency
    BackgroundScheduler = None  # type: ignore


scheduler = BackgroundScheduler() if BackgroundScheduler else None  # type: ignore

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


def start_scheduler() -> None:
    """Start APScheduler to send daily reminder emails."""

    if scheduler is None:
        return

    if not scheduler.get_jobs():
        scheduler.add_job(lambda: notify_missing_posts(), "cron", hour=20)
        scheduler.start()

