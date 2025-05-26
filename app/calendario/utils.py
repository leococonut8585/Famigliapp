"""Utility functions for Calendario."""

import json
from datetime import date, timedelta
from pathlib import Path
from typing import List, Dict

from app.utils import send_email

DEFAULT_RULES = {"max_consecutive_days": 5, "min_staff_per_day": 1}
import config

EVENTS_PATH = Path(getattr(config, "CALENDAR_FILE", "events.json"))
RULES_PATH = Path(getattr(config, "CALENDAR_RULES_FILE", "calendar_rules.json"))


def load_events() -> List[Dict[str, str]]:
    if EVENTS_PATH.exists():
        with open(EVENTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_events(events: List[Dict[str, str]]) -> None:
    with open(EVENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)


def add_event(event_date: date, title: str, description: str, employee: str) -> None:
    events = load_events()
    next_id = max((e.get("id", 0) for e in events), default=0) + 1
    events.append(
        {
            "id": next_id,
            "date": event_date.isoformat(),
            "title": title,
            "description": description,
            "employee": employee,
        }
    )
    save_events(events)
    check_rules_and_notify()


def delete_event(event_id: int) -> bool:
    events = load_events()
    new_events = [e for e in events if e.get("id") != event_id]
    if len(new_events) == len(events):
        return False
    save_events(new_events)
    check_rules_and_notify()
    return True


def load_rules() -> Dict[str, int]:
    if RULES_PATH.exists():
        with open(RULES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_RULES.copy()


def save_rules(rules: Dict[str, int]) -> None:
    with open(RULES_PATH, "w", encoding="utf-8") as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)


def move_event(event_id: int, new_date: date) -> bool:
    events = load_events()
    updated = False
    for e in events:
        if e.get("id") == event_id:
            e["date"] = new_date.isoformat()
            updated = True
            break
    if updated:
        save_events(events)
        check_rules_and_notify()
    return updated


def assign_employee(event_id: int, employee: str) -> bool:
    events = load_events()
    updated = False
    for e in events:
        if e.get("id") == event_id:
            e["employee"] = employee
            updated = True
            break
    if updated:
        save_events(events)
        check_rules_and_notify()
    return updated


def check_rules_and_notify() -> None:
    rules = load_rules()
    events = load_events()

    events_by_employee: Dict[str, List[date]] = {}
    for e in events:
        emp = e.get("employee")
        if not emp:
            continue
        events_by_employee.setdefault(emp, []).append(date.fromisoformat(e.get("date")))

    admin_email = config.USERS.get("admin", {}).get("email")

    for emp, dates in events_by_employee.items():
        dates.sort()
        count = 1
        for i in range(1, len(dates)):
            if dates[i] == dates[i - 1] + timedelta(days=1):
                count += 1
                if count > rules.get("max_consecutive_days", 9999):
                    if admin_email:
                        send_email("連勤警告", f"{emp} has excessive consecutive shifts", admin_email)
                    break
            else:
                count = 1

    events_by_date: Dict[str, int] = {}
    for e in events:
        d = e.get("date")
        events_by_date[d] = events_by_date.get(d, 0) + 1
    for d, cnt in events_by_date.items():
        if cnt < rules.get("min_staff_per_day", 1):
            if admin_email:
                send_email("人数不足警告", f"{d} has only {cnt} staff", admin_email)

