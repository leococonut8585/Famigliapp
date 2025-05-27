from datetime import date
from typing import List

try:  # pragma: no cover - optional dependency
    from apscheduler.schedulers.background import BackgroundScheduler
except Exception:  # pragma: no cover - optional dependency
    BackgroundScheduler = None  # type: ignore

scheduler = BackgroundScheduler() if BackgroundScheduler else None  # type: ignore

import config
from app.utils import send_email, get_admin_email
from . import utils


def _notify(users: List[str], subject: str, body: str) -> None:
    for u in users:
        email = config.USERS.get(u, {}).get("email")
        if email:
            send_email(subject, body, email)


def daily_reminder(today: date = date.today()) -> None:
    posts = utils.active_posts(include_expired=True)
    for p in posts:
        end = p.get("end_date")
        if not end:
            continue
        try:
            end_d = date.fromisoformat(end)
        except Exception:
            continue
        if today <= end_d:
            continue
        due = p.get("due_date")
        overdue = False
        if due:
            try:
                overdue = today > date.fromisoformat(due)
            except Exception:
                overdue = False
        if overdue:
            continue
        pending = [u for u in config.USERS if u not in p.get("feedback", {})]
        if pending:
            _notify(pending, "Corso feedback reminder", f"Please submit feedback for '{p['title']}'")


def overdue_reminder(today: date = date.today()) -> None:
    posts = utils.active_posts(include_expired=True)
    admin_email = get_admin_email()
    changed = False
    for p in posts:
        due = p.get("due_date")
        if not due:
            continue
        try:
            due_d = date.fromisoformat(due)
        except Exception:
            continue
        if today <= due_d:
            continue
        pending = [u for u in config.USERS if u not in p.get("feedback", {})]
        if not pending:
            continue
        _notify(pending, "Corso feedback overdue", f"Feedback overdue for '{p['title']}'")
        if not p.get("admin_notified") and admin_email:
            send_email(
                "Corso feedback overdue",
                f"Users pending for '{p['title']}'",
                admin_email,
            )
            p["admin_notified"] = True
            changed = True
    if changed:
        utils.save_posts(posts)


def start_scheduler() -> None:
    if scheduler is None:
        return
    if not scheduler.get_jobs():
        scheduler.add_job(lambda: daily_reminder(), "cron", hour=9)
        scheduler.add_job(lambda: overdue_reminder(), "cron", hour="*/6")
        scheduler.start()
