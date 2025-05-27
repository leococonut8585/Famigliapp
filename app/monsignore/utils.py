"""Utility functions for Monsignore posts."""

import json
from datetime import datetime
from pathlib import Path

import config

# Images only for Monsignore board
ALLOWED_EXTS = {"png", "jpg", "jpeg", "gif"}
MAX_SIZE = 10 * 1024 * 1024

MONSIGNORE_PATH = Path(getattr(config, "MONSIGNORE_FILE", "monsignore.json"))


def load_posts():
    if MONSIGNORE_PATH.exists():
        with open(MONSIGNORE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_posts(posts):
    with open(MONSIGNORE_PATH, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)


def add_post(author, body, filename=None):
    posts = load_posts()
    next_id = max((p.get("id", 0) for p in posts), default=0) + 1
    posts.append(
        {
            "id": next_id,
            "author": author,
            "body": body,
            "filename": filename,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
    )
    save_posts(posts)


def delete_post(post_id):
    posts = load_posts()
    new_posts = [p for p in posts if p.get("id") != post_id]
    if len(new_posts) == len(posts):
        return False
    save_posts(new_posts)
    return True


def filter_posts(author="", keyword=""):
    posts = load_posts()
    results = []
    for p in posts:
        if author and p.get("author") != author:
            continue
        if keyword and keyword.lower() not in p.get("body", "").lower():
            continue
        results.append(p)
    return results
