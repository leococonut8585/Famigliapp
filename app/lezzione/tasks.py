"""Tasks for Lezzione module."""

from datetime import date
from typing import List, Dict, Optional

import config
from app.utils import send_email
from . import utils


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
