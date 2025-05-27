import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

import config

INTRATTENIMENTO_PATH = Path(getattr(config, "INTRATTENIMENTO_FILE", "intrattenimento.json"))
TASKS_PATH = Path(getattr(config, "INTRATTENIMENTO_TASK_FILE", "intrattenimento_tasks.json"))

# Allow images, documents and media files as attachments
ALLOWED_EXTS = {
    "txt",
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "gif",
    "mp3",
    "mp4",
    "mov",
    "wav",
}
MAX_SIZE = 10 * 1024 * 1024
MAX_VIDEO_SIZE = 3 * 1024 * 1024 * 1024


def load_posts():
    if INTRATTENIMENTO_PATH.exists():
        with open(INTRATTENIMENTO_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_posts(posts):
    with open(INTRATTENIMENTO_PATH, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)


def add_post(author, title, body, end_date=None, filename=None):
    posts = load_posts()
    next_id = max((p.get("id", 0) for p in posts), default=0) + 1
    posts.append({
        "id": next_id,
        "author": author,
        "title": title,
        "body": body,
        "end_date": end_date.isoformat() if hasattr(end_date, "isoformat") and end_date else end_date,
        "filename": filename,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    })
    save_posts(posts)


def delete_post(post_id):
    posts = load_posts()
    new_posts = [p for p in posts if p.get("id") != post_id]
    if len(new_posts) == len(posts):
        return False
    save_posts(new_posts)
    return True


def filter_posts(include_expired: bool = False, **_unused) -> List[Dict[str, str]]:
    """Return intrattenimento posts.

    Parameters other than ``include_expired`` are ignored and kept for
    backward compatibility.
    """

    posts = load_posts()
    results: List[Dict[str, str]] = []
    now = datetime.now()
    for p in posts:
        end_date = p.get("end_date")
        if not include_expired and end_date:
            try:
                if datetime.fromisoformat(end_date) < now:
                    continue
            except ValueError:
                pass
        results.append(p)
    return results


def load_tasks() -> List[Dict[str, str]]:
    if TASKS_PATH.exists():
        with open(TASKS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_tasks(tasks: List[Dict[str, str]]) -> None:
    with open(TASKS_PATH, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


def add_task(title: str, body: str, due_date=None, filename=None) -> int:
    tasks = load_tasks()
    next_id = max((t.get("id", 0) for t in tasks), default=0) + 1
    tasks.append(
        {
            "id": next_id,
            "title": title,
            "body": body,
            "due_date": due_date.isoformat() if hasattr(due_date, "isoformat") and due_date else None,
            "filename": filename,
            "status": "open",
            "feedback": {},
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
    )
    save_tasks(tasks)
    return next_id


def finish_task(task_id: int) -> bool:
    tasks = load_tasks()
    for t in tasks:
        if t.get("id") == task_id:
            t["status"] = "finished"
            save_tasks(tasks)
            return True
    return False


def add_feedback(task_id: int, username: str, body: str) -> bool:
    tasks = load_tasks()
    for t in tasks:
        if t.get("id") == task_id and t.get("status") == "open":
            feedback = t.setdefault("feedback", {})
            feedback[username] = body
            save_tasks(tasks)
            return True
    return False


def get_active_tasks() -> List[Dict[str, str]]:
    return [t for t in load_tasks() if t.get("status") != "finished"]


def get_finished_tasks() -> List[Dict[str, str]]:
    return [t for t in load_tasks() if t.get("status") == "finished"]


def get_feedback(task_id: int, username: str) -> Optional[str]:
    tasks = load_tasks()
    for t in tasks:
        if t.get("id") == task_id:
            feedback = t.get("feedback", {})
            return feedback.get(username)
    return None
