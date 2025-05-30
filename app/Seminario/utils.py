"""Utility functions for Seminario schedules and feedback."""

import json
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any

import config


SEMINARIO_PATH = Path(getattr(config, "SEMINARIO_FILE", "seminario.json"))


def load_entries() -> List[Dict[str, Any]]:
    if SEMINARIO_PATH.exists():
        with open(SEMINARIO_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_entries(entries: List[Dict[str, Any]]) -> None:
    with open(SEMINARIO_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def add_schedule(
    author: str,
    lesson_date: date,
    title: str,
    calendar_event_type: str,
    seminar_end_date: date,
) -> None:
    entries = load_entries()
    next_id = max((int(e.get("id", 0)) for e in entries), default=0) + 1
    entries.append(
        {
            "id": next_id,
            "author": author,
            "lesson_date": lesson_date.isoformat(),  # Seminar start date
            "title": title,
            "calendar_event_type": calendar_event_type,
            "seminar_end_date": seminar_end_date.isoformat(),
            "feedback_deadline": (seminar_end_date + timedelta(days=7)).isoformat(),
            "status": "active",
            "feedback_submissions": {},
            "overdue_admin_notified_users": [], # New field
            "timestamp": datetime.now().isoformat(timespec="seconds"),  # Entry creation timestamp
        }
    )
    save_entries(entries)


def add_feedback(entry_id: int, username: str, body: str) -> bool:
    entries = load_entries()
    for e in entries:
        if e.get("id") == entry_id:
            # Ensure feedback_submissions field exists
            if "feedback_submissions" not in e:
                e["feedback_submissions"] = {}
            e["feedback_submissions"][username] = {
                "text": body,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
            }
            save_entries(entries)
            return True
    return False


def get_seminar_by_id(entry_id: int) -> Optional[Dict[str, Any]]:
    entries = load_entries()
    for e in entries:
        if e.get("id") == entry_id:
            return e
    return None


def get_kouza_seminars() -> List[Dict[str, Any]]:
    entries = load_entries()
    return [
        e
        for e in entries
        if e.get("calendar_event_type") == "kouza" and e.get("status") == "active"
    ]


def get_active_seminars() -> List[Dict[str, Any]]:
    entries = load_entries()
    return [e for e in entries if e.get("status") != "completed"]


def get_completed_seminars() -> List[Dict[str, Any]]:
    entries = load_entries()
    return [e for e in entries if e.get("status") == "completed"]


def complete_seminar(entry_id: int) -> bool:
    entries = load_entries()
    found = False
    for e in entries:
        if e.get("id") == entry_id:
            e["status"] = "completed"
            found = True
            break
    if found:
        save_entries(entries)
        return True
    return False


def get_seminars_for_feedback_page(username: str) -> List[Dict[str, Any]]:
    entries = load_entries()
    kouza_seminars = [
        e
        for e in entries
        if e.get("calendar_event_type") == "kouza" and e.get("status") == "active"
    ]
    for seminar in kouza_seminars:
        seminar["has_submitted_feedback"] = username in seminar.get(
            "feedback_submissions", {}
        )
    return kouza_seminars


def pending_feedback(today: Optional[date] = None) -> List[Dict[str, Any]]:
    today = today or date.today()
    entries = load_entries()
    results: List[Dict[str, Any]] = []
    for e in entries:
        seminar_end_date_str = e.get("seminar_end_date")
        try:
            seminar_end_date = (
                date.fromisoformat(seminar_end_date_str) if seminar_end_date_str else None
            )
        except ValueError:
            seminar_end_date = None

        if (
            e.get("calendar_event_type") == "kouza"
            and e.get("status") == "active"
            and seminar_end_date
            and seminar_end_date < today
        ):
            results.append(e)
    return results


def add_user_to_admin_notified_list(entry_id: int, username: str) -> bool:
    """Adds a username to the list of admins notified about overdue feedback for a seminar."""
    entries = load_entries()
    seminar_found = False
    user_added = False
    for seminar in entries:
        if seminar.get("id") == entry_id:
            seminar_found = True
            # Ensure the list exists, using setdefault to initialize if not present
            notified_list = seminar.setdefault("overdue_admin_notified_users", [])
            if username not in notified_list:
                notified_list.append(username)
                user_added = True
            break  # Exit loop once seminar is found

    if seminar_found and user_added:
        save_entries(entries)
        return True
    return False


def get_admin_users() -> List[Dict[str, Any]]:
    """Retrieves a list of admin users with email addresses from config."""
    admin_users: List[Dict[str, Any]] = []
    if hasattr(config, "USERS") and isinstance(config.USERS, dict):
        for user_name, user_data in config.USERS.items():
            if isinstance(user_data, dict) and \
               user_data.get("role") == "admin" and \
               user_data.get("email"): # Ensure email exists and is not empty
                # Add the username to the user_data if it's not already there
                # or if you want to ensure it's present under a specific key.
                # For now, just returning the user_data dict.
                # user_data_with_username = user_data.copy()
                # user_data_with_username['username'] = user_name
                admin_users.append(user_data) # user_data already contains all info
    return admin_users
