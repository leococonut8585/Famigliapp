"""Utility functions for Calendario."""

import json
from datetime import date, timedelta
from pathlib import Path
from typing import List, Dict, Set, Optional, Iterable

from app.utils import send_email


def _notify_all(subject: str, body: str) -> None:
    """Send email notification to all configured users."""
    for info in config.USERS.values():
        email = info.get("email")
        if email:
            send_email(subject, body, email)


def _notify_event(action: str, event: Dict[str, str], old: str = "") -> None:
    """Notify all users about calendar event changes."""
    title = event.get("title", "")
    date_str = event.get("date", "")
    if action == "add":
        body = f"{date_str} に '{title}' が追加されました"
    elif action == "delete":
        body = f"{date_str} の '{title}' が削除されました"
    elif action == "move":
        body = f"'{title}' の日付が {old} から {date_str} に変更されました"
    elif action == "assign":
        emp = event.get("employee", "")
        body = f"{date_str} の '{title}' の担当が {emp} に設定されました"
    else:
        body = f"{date_str}: {title} updated"
    _notify_all("カレンダー更新", body)

DEFAULT_RULES = {
    "max_consecutive_days": 5,
    "min_staff_per_day": 1,
    # 組み合わせに関する追加ルール
    "forbidden_pairs": [],  # [["taro", "hanako"], ...]
    "required_pairs": [],   # [["alice", "bob"], ...]
    # 属性別の勤務者チェックに使用する設定
    "required_attributes": {},  # {"A": 1, "B": 1}
    "employee_attributes": {},  # {"taro": "A", "hanako": "B"}
}
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


def add_event(
    event_date: date,
    title: str,
    description: str,
    employee: str,
    category: str = "other",
    participants: Optional[Iterable[str]] = None,
) -> None:
    events = load_events()
    next_id = max((e.get("id", 0) for e in events), default=0) + 1
    events.append(
        {
            "id": next_id,
            "date": event_date.isoformat(),
            "title": title,
            "description": description,
            "employee": employee,
            "category": category,
            "participants": list(participants or []),
        }
    )
    save_events(events)
    check_rules_and_notify()
    _notify_event("add", events[-1])

    if category == "lesson":
        from app.corso import utils as corso_utils

        corso_utils.add_post(
            "system",
            title,
            description or "lesson scheduled",
            None,
            None,
        )


def delete_event(event_id: int) -> bool:
    events = load_events()
    event = next((e for e in events if e.get("id") == event_id), None)
    new_events = [e for e in events if e.get("id") != event_id]
    if len(new_events) == len(events):
        return False
    save_events(new_events)
    check_rules_and_notify()
    if event:
        _notify_event("delete", event)
    return True


def load_rules() -> Dict[str, int]:
    if RULES_PATH.exists():
        with open(RULES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_RULES.copy()


def save_rules(rules: Dict[str, int]) -> None:
    with open(RULES_PATH, "w", encoding="utf-8") as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)


def parse_pairs(text: str) -> List[List[str]]:
    """Parse pair text like 'a-b,c-d' into list of pairs."""
    pairs: List[List[str]] = []
    for item in text.split(','):
        names = [p.strip() for p in item.split('-') if p.strip()]
        if len(names) >= 2:
            pairs.append(names[:2])
    return pairs


def parse_kv(text: str) -> Dict[str, object]:
    """Parse key:value pairs. Values may contain '|' to represent lists."""
    result: Dict[str, object] = {}
    for item in text.split(','):
        if ':' not in item:
            continue
        k, v = item.split(':', 1)
        k = k.strip()
        v = v.strip()
        if not k or not v:
            continue
        if '|' in v:
            result[k] = [p.strip() for p in v.split('|') if p.strip()]
        else:
            result[k] = v
    return result


def parse_kv_int(text: str) -> Dict[str, int]:
    result: Dict[str, int] = {}
    for item in text.split(','):
        if ':' not in item:
            continue
        k, v = item.split(':', 1)
        k = k.strip()
        v = v.strip()
        if not k or not v:
            continue
        try:
            result[k] = int(v)
        except ValueError:
            pass
    return result


def move_event(event_id: int, new_date: date) -> bool:
    events = load_events()
    updated = False
    changed = None
    for e in events:
        if e.get("id") == event_id:
            old = e.get("date", "")
            e["date"] = new_date.isoformat()
            updated = True
            changed = e
            break
    if updated:
        save_events(events)
        check_rules_and_notify()
        if changed:
            _notify_event("move", changed, old)
    return updated


def assign_employee(event_id: int, employee: str) -> bool:
    events = load_events()
    updated = False
    changed = None
    for e in events:
        if e.get("id") == event_id:
            e["employee"] = employee
            updated = True
            changed = e
            break
    if updated:
        save_events(events)
        check_rules_and_notify()
        if changed:
            _notify_event("assign", changed)
    return updated


def set_shift_schedule(month: date, schedule: Dict[str, List[str]]) -> None:
    """Replace shift events for the given month based on schedule."""
    events = load_events()
    events = [
        e
        for e in events
        if not (
            e.get("category") == "shift"
            and e.get("date", "").startswith(month.strftime("%Y-%m"))
        )
    ]
    next_id = max((e.get("id", 0) for e in events), default=0) + 1
    new_events = []
    for day_str, emps in schedule.items():
        for emp in emps:
            new_events.append(
                {
                    "id": next_id,
                    "date": day_str,
                    "title": emp,
                    "description": "",
                    "employee": emp,
                    "category": "shift",
                    "participants": [],
                }
            )
            next_id += 1
    events.extend(new_events)
    save_events(events)
    check_rules_and_notify()
    for ev in new_events:
        _notify_event("add", ev)


def check_rules_and_notify() -> None:
    rules = load_rules()
    events = load_events()

    events_by_employee: Dict[str, List[date]] = {}
    for e in events:
        emp = e.get("employee")
        if not emp:
            continue
        events_by_employee.setdefault(emp, []).append(date.fromisoformat(e.get("date")))

    admin_email = utils.get_admin_email()

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

    # --- 以下は追加のルールチェック ---
    events_by_date_emps: Dict[str, List[str]] = {}
    for e in events:
        emp = e.get("employee")
        if not emp:
            continue
        d = e.get("date")
        events_by_date_emps.setdefault(d, []).append(emp)

    forbidden_pairs = rules.get("forbidden_pairs", [])
    required_pairs = rules.get("required_pairs", [])
    required_attrs = rules.get("required_attributes", {})
    emp_attrs = rules.get("employee_attributes", {})

    for d, emps in events_by_date_emps.items():
        # forbiddens
        for pair in forbidden_pairs:
            if len(pair) >= 2 and pair[0] in emps and pair[1] in emps:
                if admin_email:
                    send_email(
                        "組み合わせ禁止警告",
                        f"{pair[0]} and {pair[1]} overlap on {d}",
                        admin_email,
                    )
        # required pairs
        for pair in required_pairs:
            if len(pair) >= 2:
                a, b = pair[0], pair[1]
                if (a in emps) ^ (b in emps):
                    if admin_email:
                        send_email(
                            "組み合わせ不足警告",
                            f"{a} and {b} must work together on {d}",
                            admin_email,
                        )

        if required_attrs:
            attr_counts: Dict[str, int] = {k: 0 for k in required_attrs}
            for emp in emps:
                attr = emp_attrs.get(emp)
                if isinstance(attr, list):
                    for a in attr:
                        if a in attr_counts:
                            attr_counts[a] += 1
                elif attr in attr_counts:
                    attr_counts[attr] += 1
            for attr, min_cnt in required_attrs.items():
                if attr_counts.get(attr, 0) < min_cnt:
                    if admin_email:
                        send_email(
                            "属性不足警告",
                            f"{d} lacks enough {attr} staff",
                            admin_email,
                        )


def compute_employee_stats(
    start: Optional[date] = None, end: Optional[date] = None
) -> Dict[str, Dict[str, int]]:
    """Return work/off day counts for each employee.

    Parameters
    ----------
    start, end : Optional[date]
        Date range to aggregate. When both are provided, ``off_days`` will
        be included in the result based on the number of days in the range.
    """

    events = load_events()
    by_emp: Dict[str, Set[date]] = {}
    for e in events:
        emp = e.get("employee")
        d_str = e.get("date")
        if not emp or not d_str:
            continue
        try:
            d = date.fromisoformat(d_str)
        except ValueError:
            continue
        if start and d < start:
            continue
        if end and d > end:
            continue
        by_emp.setdefault(emp, set()).add(d)

    total_days = None
    if start is not None and end is not None:
        total_days = (end - start).days + 1

    stats: Dict[str, Dict[str, int]] = {}
    for emp, dates in by_emp.items():
        work = len(dates)
        data: Dict[str, int] = {"work_days": work}
        if total_days is not None:
            data["off_days"] = total_days - work
        stats[emp] = data

    return stats


