"""Utility functions for Calendario."""

import json
from datetime import date
from pathlib import Path
from typing import List, Dict

import config

EVENTS_PATH = Path(getattr(config, "CALENDAR_FILE", "events.json"))


def load_events() -> List[Dict[str, str]]:
    if EVENTS_PATH.exists():
        with open(EVENTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_events(events: List[Dict[str, str]]) -> None:
    with open(EVENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)


def add_event(event_date: date, title: str, description: str) -> None:
    events = load_events()
    next_id = max((e.get("id", 0) for e in events), default=0) + 1
    events.append(
        {
            "id": next_id,
            "date": event_date.isoformat(),
            "title": title,
            "description": description,
        }
    )
    save_events(events)


def delete_event(event_id: int) -> bool:
    events = load_events()
    new_events = [e for e in events if e.get("id") != event_id]
    if len(new_events) == len(events):
        return False
    save_events(new_events)
    return True

