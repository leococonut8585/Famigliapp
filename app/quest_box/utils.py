"""Utility functions for Quest Box."""

import json
from pathlib import Path
from datetime import datetime, date
from typing import Optional, List

import config

QUESTS_PATH = Path(getattr(config, "QUEST_BOX_FILE", "quests.json"))


def load_quests():
    if QUESTS_PATH.exists():
        with open(QUESTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_quests(quests):
    with open(QUESTS_PATH, "w", encoding="utf-8") as f:
        json.dump(quests, f, ensure_ascii=False, indent=2)


def add_quest(
    author: str,
    title: str,
    body: str,
    conditions: str = "",
    capacity: int = 0,
    due_date: Optional[date] = None,
    assigned_to: Optional[List[str]] = None,
    reward: str = "",
) -> None:
    """Add a quest entry."""

    quests = load_quests()
    next_id = max((q.get("id", 0) for q in quests), default=0) + 1
    quests.append(
        {
            "id": next_id,
            "author": author,
            "title": title,
            "body": body,
            "conditions": conditions,
            "capacity": capacity,
            "due_date": due_date.isoformat() if hasattr(due_date, "isoformat") and due_date else None,
            "assigned_to": assigned_to or [],
            "status": "open",
            "accepted_by": "",
            "reward": reward,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
    )
    save_quests(quests)


def accept_quest(quest_id, username):
    quests = load_quests()
    for q in quests:
        if q.get("id") == quest_id and q.get("status") == "open":
            q["status"] = "accepted"
            q["accepted_by"] = username
            save_quests(quests)
            return True
    return False


def complete_quest(quest_id):
    quests = load_quests()
    for q in quests:
        if q.get("id") == quest_id and q.get("status") in {"accepted", "open"}:
            q["status"] = "completed"
            save_quests(quests)
            return True
    return False


def delete_quest(quest_id):
    quests = load_quests()
    new_quests = [q for q in quests if q.get("id") != quest_id]
    if len(new_quests) == len(quests):
        return False
    save_quests(new_quests)
    return True


def set_reward(quest_id, reward):
    quests = load_quests()
    for q in quests:
        if q.get("id") == quest_id:
            q["reward"] = reward
            save_quests(quests)
            return True
    return False


def update_quest(
    quest_id: int,
    title: str,
    body: str,
    conditions: str = "",
    capacity: int = 0,
    due_date: Optional[date] = None,
    assigned_to: Optional[List[str]] = None,
    reward: str = "",
) -> bool:
    """Update an existing quest entry.

    Parameters
    ----------
    quest_id : int
        ID of the quest to update.
    title : str
        Updated title.
    body : str
        Updated body text.
    due_date : Optional[date], optional
        New due date, by default ``None``.
    assigned_to : str, optional
        Assigned user, by default ``""``.

    Returns
    -------
    bool
        ``True`` if quest existed and was updated.
    """

    quests = load_quests()
    for q in quests:
        if q.get("id") == quest_id:
            q["title"] = title
            q["body"] = body
            q["conditions"] = conditions
            q["capacity"] = capacity
            q["due_date"] = (
                due_date.isoformat() if hasattr(due_date, "isoformat") and due_date else None
            )
            q["assigned_to"] = assigned_to or []
            q["reward"] = reward
            save_quests(quests)
            return True
    return False
