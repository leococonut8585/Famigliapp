"""Utility functions for Corso posts."""

import json
from datetime import datetime, timedelta, date
from pathlib import Path

import config

# Allow only documents and images for attachments
ALLOWED_EXTS = {
    "txt",
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "gif",
}
MAX_SIZE = 10 * 1024 * 1024

CORSO_PATH = Path(getattr(config, "CORSO_FILE", "corso.json"))


def load_posts():
    """Load Corso posts from JSON file."""

    if CORSO_PATH.exists():
        with open(CORSO_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_posts(posts):
    """Save posts list to JSON file."""

    with open(CORSO_PATH, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)


def add_post(author, title, body, end_date=None, filename=None):
    """Add a new Corso post."""

    posts = load_posts()
    next_id = max((p.get("id", 0) for p in posts), default=0) + 1
    due = None
    if end_date:
        try:
            due = (end_date + timedelta(days=3)).isoformat()
        except Exception:
            pass
    posts.append(
        {
            "id": next_id,
            "author": author,
            "title": title,
            "body": body,
            "end_date": end_date.isoformat() if hasattr(end_date, "isoformat") and end_date else end_date,
            "due_date": due,
            "filename": filename,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "feedback": {},
            "archived": False,
            "admin_notified": False,
        }
    )
    save_posts(posts)


def delete_post(post_id):
    """Delete a Corso post by ID."""

    posts = load_posts()
    new_posts = [p for p in posts if p.get("id") != post_id]
    if len(new_posts) == len(posts):
        return False
    save_posts(new_posts)
    return True


def add_feedback(post_id: int, username: str, body: str) -> bool:
    """Add feedback text for a corso."""

    posts = load_posts()
    for p in posts:
        if p.get("id") == post_id:
            fb = p.setdefault("feedback", {})
            fb[username] = {
                "body": body,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
            }
            save_posts(posts)
            return True
    return False


def finish_post(post_id: int) -> bool:
    """Mark corso as archived."""

    posts = load_posts()
    for p in posts:
        if p.get("id") == post_id:
            p["archived"] = True
            save_posts(posts)
            return True
    return False


def active_posts(include_expired: bool = False):
    posts = load_posts()
    return [p for p in posts if not p.get("archived") and (include_expired or not _is_expired(p))]


def archived_posts():
    posts = load_posts()
    return [p for p in posts if p.get("archived")]


def _is_expired(post: dict) -> bool:
    end_date = post.get("end_date")
    if end_date:
        try:
            return datetime.fromisoformat(end_date) < datetime.now()
        except ValueError:
            pass
    return False


def filter_posts(author="", keyword="", include_expired=False):
    """Filter posts by author, keyword and expiration."""

    posts = load_posts()
    results = []
    now = datetime.now()
    for p in posts:
        if author and p.get("author") != author:
            continue
        if keyword:
            title = p.get("title", "")
            body = p.get("body", "")
            if keyword.lower() not in (title + body).lower():
                continue
        end_date = p.get("end_date")
        if not include_expired and end_date:
            try:
                if datetime.fromisoformat(end_date) < now:
                    continue
            except ValueError:
                pass
        results.append(p)
    return results

