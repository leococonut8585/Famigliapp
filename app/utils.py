import json
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta

import config

POINTS_PATH = Path(config.POINTS_FILE)
POINTS_HISTORY_PATH = Path(config.POINTS_HISTORY_FILE)
POSTS_PATH = Path(config.POSTS_FILE)


def load_points() -> Dict[str, Dict[str, int]]:
    if POINTS_PATH.exists():
        with open(POINTS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {}


def load_points_history() -> List[Dict[str, str]]:
    if POINTS_HISTORY_PATH.exists():
        with open(POINTS_HISTORY_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def filter_points_history(
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    username: str = "",
) -> List[Dict[str, str]]:
    """履歴を開始日・終了日・ユーザー名でフィルタリングして返す。"""

    history = load_points_history()
    results: List[Dict[str, str]] = []

    for entry in history:
        ts = datetime.fromisoformat(entry.get("timestamp"))
        if start and ts < start:
            continue
        if end and ts > end:
            continue
        if username and entry.get("username") != username:
            continue
        results.append(entry)

    return results


def log_points_change(username: str, delta_a: int, delta_o: int, timestamp: Optional[datetime] = None) -> None:
    history = load_points_history()
    ts = timestamp or datetime.now()
    history.append({
        'username': username,
        'A': delta_a,
        'O': delta_o,
        'timestamp': ts.isoformat(timespec='seconds'),
    })
    with open(POINTS_HISTORY_PATH, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


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


def filter_posts(
    category: str = "",
    author: str = "",
    keyword: str = "",
) -> List[Dict[str, str]]:
    """Filter posts by category, author and keyword."""
    posts = load_posts()
    results: List[Dict[str, str]] = []
    for p in posts:
        if category and p.get("category") != category:
            continue
        if author and p.get("author") != author:
            continue
        if keyword and keyword not in p.get("text", ""):
            continue
        results.append(p)
    return results


def login(username: str, password: str) -> Optional[Dict[str, str]]:
    user = config.USERS.get(username)
    if user and user['password'] == password:
        return {
            'username': username,
            'role': user['role'],
            'email': user['email']
        }
    return None


def get_ranking(
    metric: str = "A",
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    period: Optional[str] = None,
) -> List[Tuple[str, int]]:
    """Return ranking list of users by the specified metric.

    Parameters
    ----------
    metric : str
        "A", "O", or "U". "U" represents A - O.

    Returns
    -------
    List[Tuple[str, int]]
        Sorted list of (username, value) pairs in descending order.
    """
    metric = metric.upper()

    if period:
        period = period.lower()
        now = end or datetime.now()
        if period == "weekly":
            start = now - timedelta(days=7)
        elif period == "monthly":
            start = now.replace(day=1)
        elif period == "yearly":
            start = now.replace(month=1, day=1)

    if start or end:
        if start is None:
            start = datetime.min
        if end is None:
            end = datetime.max
        history = load_points_history()
        ranking_dict: Dict[str, int] = {}
        for entry in history:
            ts = datetime.fromisoformat(entry.get("timestamp"))
            if start <= ts <= end:
                username = entry.get("username")
                delta_a = entry.get("A", 0)
                delta_o = entry.get("O", 0)
                if metric == "U":
                    value = delta_a - delta_o
                elif metric == "A":
                    value = delta_a
                else:
                    value = delta_o
                ranking_dict[username] = ranking_dict.get(username, 0) + value
        ranking = sorted(ranking_dict.items(), key=lambda x: x[1], reverse=True)
        return ranking
    else:
        points = load_points()
        ranking: List[Tuple[str, int]] = []
        for user, p in points.items():
            if metric == "U":
                value = p.get("A", 0) - p.get("O", 0)
            else:
                value = p.get(metric, 0)
            ranking.append((user, value))
        ranking.sort(key=lambda x: x[1], reverse=True)
        return ranking
