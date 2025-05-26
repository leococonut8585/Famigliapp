import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

import config

INTRATTENIMENTO_PATH = Path(getattr(config, "INTRATTENIMENTO_FILE", "intrattenimento.json"))


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


def filter_posts(
    author: str = "",
    keyword: str = "",
    include_expired: bool = False,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> List[Dict[str, str]]:
    """Filter intrattenimento posts by various criteria."""

    posts = load_posts()
    results: List[Dict[str, str]] = []
    now = datetime.now()
    for p in posts:
        if author and p.get("author") != author:
            continue
        if keyword:
            title = p.get("title", "")
            body = p.get("body", "")
            if keyword.lower() not in (title + body).lower():
                continue
        ts_str = p.get("timestamp")
        if start or end:
            try:
                ts = datetime.fromisoformat(ts_str) if ts_str else None
            except Exception:
                ts = None
            if start and ts and ts < start:
                continue
            if end and ts and ts > end:
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
