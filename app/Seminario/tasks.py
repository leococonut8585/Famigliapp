"""Background tasks for Seminario blueprint."""

from datetime import date, timedelta, datetime # Added datetime for timestamping
from typing import List, Dict, Any, Optional # Added Any

try:  # pragma: no cover - optional dependency
    from apscheduler.schedulers.background import BackgroundScheduler
except ImportError:  # pragma: no cover - optional dependency
    BackgroundScheduler = None

import config
from app.utils import send_email
from . import utils


scheduler = BackgroundScheduler() if BackgroundScheduler else None


def notify_pending_feedback() -> List[Dict[str, Any]]:
    """
    Sends reminder emails for seminars lacking feedback.
    - Daily reminders for users if feedback is due (after seminar end, before deadline).
    - Overdue notifications for users if feedback is past deadline.
    - Alerts admins if a user's feedback is overdue and admin hasn't been notified for that user/seminar pair.
    Returns a list of notification records.
    """
    today = date.today()
    # utils.pending_feedback returns active 'kouza' seminars where seminar_end_date < today
    relevant_seminars = utils.pending_feedback(today)

    admin_users = utils.get_admin_users()  # List of admin user dicts with emails
    notified_actions: List[Dict[str, Any]] = []

    for seminar in relevant_seminars:
        seminar_id = seminar.get("id")
        seminar_title = seminar.get("title", "N/A")
        feedback_deadline_str = seminar.get("feedback_deadline")

        if not seminar_id or not feedback_deadline_str:
            # Log error: Missing critical seminar information
            continue

        try:
            # seminar_end_date_obj = date.fromisoformat(seminar.get("seminar_end_date")) # Provided by pending_feedback
            feedback_deadline_obj = date.fromisoformat(feedback_deadline_str)
        except ValueError:
            # Log error: Invalid date format in seminar data
            continue

        for username_key, user_config_data in config.USERS.items():
            if user_config_data.get('role') != 'admin' and user_config_data.get('email'):
                user_email = user_config_data['email']

                submitted = username_key in seminar.get("feedback_submissions", {})

                if not submitted:
                    current_time_iso = datetime.now().isoformat()
                    common_notification_data = {
                        'user': username_key,
                        'seminar_id': seminar_id,
                        'seminar_title': seminar_title,
                        'timestamp': current_time_iso
                    }

                    # Daily Reminder (seminar ended, feedback not submitted, deadline not passed)
                    if today <= feedback_deadline_obj:
                        send_email(
                            "Seminar Feedback Reminder",
                            f"Please submit feedback for '{seminar_title}'. Deadline: {feedback_deadline_str}",
                            user_email
                        )
                        notified_actions.append({**common_notification_data, 'status': 'notified_due'})

                    # Overdue Notification (deadline passed, feedback not submitted)
                    else: # today > feedback_deadline_obj
                        send_email(
                            "OVERDUE: Seminar Feedback Required",
                            f"Your feedback for '{seminar_title}' is overdue. Please submit it as soon as possible. Original deadline was {feedback_deadline_str}.",
                            user_email
                        )
                        notified_actions.append({**common_notification_data, 'status': 'notified_overdue_user'})

                        # Admin Notification Logic for this overdue, un-submitted feedback
                        overdue_admin_notified_list = seminar.get("overdue_admin_notified_users", [])
                        if username_key not in overdue_admin_notified_list:
                            for admin_user_details in admin_users:
                                admin_email = admin_user_details.get("email")
                                if admin_email: # Should always be true due to get_admin_users logic
                                    send_email(
                                        "User Feedback Overdue Alert",
                                        f"User '{username_key}' has not submitted feedback for seminar '{seminar_title}' (ID: {seminar_id}) which was due on {feedback_deadline_str}.",
                                        admin_email
                                    )

                            if utils.add_user_to_admin_notified_list(seminar_id, username_key):
                                notified_actions.append({
                                    **common_notification_data,
                                    'status': 'notified_overdue_admin',
                                    'admin_notified_count': len(admin_users)
                                })
                            # else: Log failure to add user to notified list if necessary

    return notified_actions


def start_scheduler() -> None:
    """Start APScheduler job to send daily feedback reminders.
    The job runs daily at 9 AM.
    """
    if scheduler is None:  # pragma: no cover
        return

    if not scheduler.get_jobs(): # Ensure only one job is scheduled
        scheduler.add_job(
            notify_pending_feedback,  # No lambda, no arguments
            "cron",
            hour=9,  # Runs daily at 9 AM
        )
        scheduler.start() # pragma: no cover
