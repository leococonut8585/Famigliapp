"""Background tasks for Monsignore (Kadai) blueprint."""

from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional

try:  # pragma: no cover - optional dependency
    from apscheduler.schedulers.background import BackgroundScheduler
except ImportError:  # pragma: no cover - optional dependency
    BackgroundScheduler = None

import config
from app.utils import send_email # For sending emails
from . import utils # Monsignore specific utilities

scheduler = BackgroundScheduler() if BackgroundScheduler else None


def notify_kadai_feedback_reminders() -> List[Dict[str, Any]]:
    """
    Sends reminder emails for Kadai entries lacking feedback.
    - Daily reminders for users if feedback is due (after Kadai creation, before deadline).
    - Overdue notifications for users if feedback is past deadline.
    - Alerts admins if a user's feedback is overdue and admin hasn't been notified for that user/kadai pair.
    Returns a list of notification records.
    """
    today = date.today()
    active_kadai_entries = utils.get_active_kadai_entries()

    general_users_with_email: Dict[str, Dict[str, Any]] = {}
    if hasattr(config, "USERS") and isinstance(config.USERS, dict):
        for username, user_data in config.USERS.items():
            if isinstance(user_data, dict) and \
               user_data.get("role") != "admin" and \
               user_data.get("email"):
                general_users_with_email[username] = user_data

    admin_users_with_email = utils.get_admin_users()

    notified_actions: List[Dict[str, Any]] = []
    current_time_iso = datetime.now().isoformat()

    for kadai in active_kadai_entries:
        kadai_id = kadai.get("id")
        kadai_title = kadai.get("title", "N/A")
        feedback_deadline_str = kadai.get("feedback_deadline")
        kadai_creation_ts_str = kadai.get("timestamp")

        if not kadai_id or not feedback_deadline_str or not kadai_creation_ts_str:
            continue

        try:
            feedback_deadline_obj = datetime.fromisoformat(feedback_deadline_str).date()
            kadai_creation_obj = datetime.fromisoformat(kadai_creation_ts_str).date()
        except ValueError:
            continue

        for username, user_details in general_users_with_email.items():
            user_email = user_details['email']
            submitted = username in kadai.get("feedback_submissions", {})

            if not submitted:
                common_notification_data = {
                    'user': username,
                    'kadai_id': kadai_id,
                    'kadai_title': kadai_title,
                    'timestamp': current_time_iso
                }

                if today <= feedback_deadline_obj and today > kadai_creation_obj:
                    send_email(
                        f"「{kadai_title}」の感想をお待ちしています",
                        f"「{kadai_title}」に関するあなたの感想をお待ちしています。\n締切: {feedback_deadline_str.split('T')[0]}\n提出はこちらから。",
                        user_email
                    )
                    notified_actions.append({**common_notification_data, 'status': 'notified_due'})

                elif today > feedback_deadline_obj:
                    send_email(
                        f"【至急】「{kadai_title}」の感想が未提出です",
                        f"「{kadai_title}」に関するあなたの感想が未提出です。\n締切は {feedback_deadline_str.split('T')[0]} でした。\n至急ご提出ください。",
                        user_email
                    )
                    notified_actions.append({**common_notification_data, 'status': 'notified_overdue_user'})

                    overdue_admin_notified_list = kadai.get("overdue_admin_notified_users", [])
                    if username not in overdue_admin_notified_list:
                        for admin_user in admin_users_with_email:
                            admin_email = admin_user.get("email")
                            if admin_email:
                                send_email(
                                    "ユーザーの感想期限超過アラート",
                                    f"ユーザー「{username}」が「言葉」の「{kadai_title}」(ID: {kadai_id}) に対する感想を期限超過しています。\n締切: {feedback_deadline_str.split('T')[0]}.",
                                    admin_email
                                )

                        if utils.add_user_to_kadai_admin_notified_list(kadai_id, username):
                             notified_actions.append({
                                **common_notification_data,
                                'status': 'notified_overdue_admin',
                                'admin_notified_count': len(admin_users_with_email)
                            })

    return notified_actions


def archive_old_kadai_entries() -> List[int]:
    """
    Archives Kadai entries older than 48 hours from their creation time.
    Returns a list of IDs of the archived entries.
    """
    now = datetime.now()
    active_kadai_entries = utils.get_active_kadai_entries()
    archived_ids: List[int] = []

    for kadai in active_kadai_entries:
        kadai_id = kadai.get("id")
        creation_timestamp_str = kadai.get("timestamp")

        if not kadai_id or not creation_timestamp_str:
            # Log error or skip if essential data is missing
            continue

        try:
            creation_dt = datetime.fromisoformat(creation_timestamp_str)
        except ValueError:
            # Log error or skip if timestamp format is invalid
            continue

        archive_trigger_time = creation_dt + timedelta(hours=48)

        if now >= archive_trigger_time:
            if utils.archive_kadai_entry(kadai_id):
                archived_ids.append(kadai_id)
                # Optional: Log("Archived Kadai ID: {kadai_id}")

    return archived_ids


def start_scheduler() -> None:
    """
    Starts APScheduler jobs for:
    - Sending daily Kadai feedback reminders (10 AM).
    - Archiving old Kadai entries (01:05 AM).
    """
    if scheduler is None:  # pragma: no cover
        return

    # Check if jobs are already scheduled to prevent duplicates if called multiple times
    # This simplistic check assumes job IDs are not explicitly set or are predictable.
    # A more robust check might involve inspecting scheduler.get_jobs() more thoroughly.
    if not scheduler.get_jobs():
        scheduler.add_job(
            notify_kadai_feedback_reminders,
            "cron",
            hour=10,  # Runs daily at 10 AM
            id="notify_kadai_reminders" # Added job ID
        )
        scheduler.add_job(
            archive_old_kadai_entries,
            "cron",
            hour=1,   # Runs daily at 01:05 AM
            minute=5,
            id="archive_old_kadai" # Added job ID
        )
        try: # pragma: no cover
            scheduler.start()
        except (KeyboardInterrupt, SystemExit): # pragma: no cover
            pass # Allow clean shutdown
        except Exception as e: # pragma: no cover
            # Log scheduler start error if any
            print(f"Error starting scheduler: {e}")

    elif not scheduler.running: # pragma: no cover
        # If jobs are defined but scheduler isn't running (e.g., after a stop)
        try:
            scheduler.start(paused=False) # Start without re-adding jobs
        except Exception as e:
            print(f"Error restarting scheduler: {e}")
