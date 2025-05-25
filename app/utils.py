import json
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

import config

POINTS_PATH = Path(config.POINTS_FILE)
POSTS_PATH = Path(config.POSTS_FILE)


def load_points() -> Dict[str, Dict[str, int]]:
    if POINTS_PATH.exists():
        with open(POINTS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {}


def save_points(points: Dict[str, Dict[str, int]]) -> None:
    with open(POINTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(points, f, ensure_ascii=False, indent=2)


def load_posts() -> List[Dict[str, str]]:
    if POSTS_PATH.exists():
        with open(POSTS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_posts(posts: List[Dict[str, str]]) -> None:
    with open(POSTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)


def add_post(author: str, category: str, text: str) -> None:
    posts = load_posts()
    next_id = max((p.get('id', 0) for p in posts), default=0) + 1
    post = {
        'id': next_id,
        'author': author,
        'category': category,
        'text': text,
        'timestamp': datetime.now().isoformat(timespec='seconds'),
    }
    posts.append(post)
    save_posts(posts)


def delete_post(post_id: int) -> bool:
    posts = load_posts()
    new_posts = [p for p in posts if p.get('id') != post_id]
    if len(new_posts) == len(posts):
        return False
    save_posts(new_posts)
    return True


def login(username: str, password: str) -> Optional[Dict[str, str]]:
    user = config.USERS.get(username)
    if user and user['password'] == password:
        return {
            'username': username,
            'role': user['role'],
            'email': user['email']
        }
    return None
