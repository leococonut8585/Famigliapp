"""Background tasks for Seminario blueprint."""

from datetime import date, timedelta
from typing import List, Dict, Optional

try:  # pragma: no cover - optional dependency
    from apscheduler.schedulers.background import BackgroundScheduler
except Exception:  # pragma: no cover - optional dependency
    BackgroundScheduler = None  # type: ignore

import config
from app.utils import send_email
from . import utils


scheduler = BackgroundScheduler() if BackgroundScheduler else None  # type: ignore


def notify_pending_feedback(
    since: date, today: Optional[date] = None
) -> List[Dict[str, str]]:
    """Send reminder emails for lessons lacking feedback.

    Parameters
    ----------
    since : date
        Notify only entries whose lesson date is on or after this date.
    today : Optional[date]
        Date used to determine which lessons are considered past. Defaults to
        ``date.today()``.

    Returns
    -------
    List[Dict[str, str]]
        Entries for which a notification was sent.
    """

    today = today or date.today()
    pending = utils.pending_feedback(today)
    notified: List[Dict[str, str]] = []

    for entry in pending:
        d_str = entry.get("lesson_date")
        try:
            d = date.fromisoformat(d_str) if d_str else None
        except ValueError:
            d = None
        if not d or d < since:
            continue
        username = entry.get("author")
        email = config.USERS.get(username, {}).get("email")
        if email:
            title = entry.get("title", "")
            send_email("Feedback reminder", f"Please submit feedback for '{title}'", email)
            notified.append(entry)

    return notified


def start_scheduler() -> None:
    """Start APScheduler job to send daily feedback reminders."""

    if scheduler is None:
        return

    if not scheduler.get_jobs():
        scheduler.add_job(
            lambda: notify_pending_feedback(date.today() - timedelta(days=7)),
            "cron",
            hour=9,
        )
        scheduler.start()
