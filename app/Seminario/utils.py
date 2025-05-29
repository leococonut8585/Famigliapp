"""Utility functions for Seminario schedules and feedback."""

import json
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Optional

import config



SEMINARIO_PATH = Path(getattr(config, "SEMINARIO_FILE", "seminario.json")) # MODIFIED


def load_entries() -> List[Dict[str, str]]:
    if SEMINARIO_PATH.exists(): # MODIFIED
        with open(SEMINARIO_PATH, "r", encoding="utf-8") as f: # MODIFIED
            return json.load(f)
    return []


def save_entries(entries: List[Dict[str, str]]) -> None:

    with open(SEMINARIO_PATH, "w", encoding="utf-8") as f: # MODIFIED
        json.dump(entries, f, ensure_ascii=False, indent=2)


def add_schedule(author: str, lesson_date: date, title: str) -> None:
    entries = load_entries()
    next_id = max((e.get("id", 0) for e in entries), default=0) + 1
    entries.append(
        {
            "id": next_id,
            "author": author,
            "lesson_date": lesson_date.isoformat(),
            "title": title,
            "feedback": "",
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
    )
    save_entries(entries)


def add_feedback(entry_id: int, body: str) -> bool:
    entries = load_entries()
    for e in entries:
        if e.get("id") == entry_id:
            e["feedback"] = body
            e["feedback_timestamp"] = datetime.now().isoformat(timespec="seconds")
            save_entries(entries)
            return True
    return False


def pending_feedback(today: Optional[date] = None) -> List[Dict[str, str]]:
    today = today or date.today()
    entries = load_entries()
    results: List[Dict[str, str]] = []
    for e in entries:
        d_str = e.get("lesson_date")
        try:
            d = date.fromisoformat(d_str) if d_str else None
        except ValueError:
            d = None
        if d and d < today and not e.get("feedback"):
            results.append(e)
    return results

