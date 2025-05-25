import json
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta

try:
    from flask import current_app
except Exception:  # pragma: no cover - optional dependency
    current_app = None  # type: ignore

try:
    from . import db
    from .models import User, Post, PointsHistory  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    db = None  # type: ignore
    User = Post = PointsHistory = None  # type: ignore

import config

POINTS_PATH = Path(config.POINTS_FILE)
POINTS_HISTORY_PATH = Path(config.POINTS_HISTORY_FILE)
POSTS_PATH = Path(config.POSTS_FILE)


def _use_db() -> bool:
    """Return True if a database connection is available."""

    if db is None or current_app is None:
        return False
    try:  # pragma: no cover - runtime check
        db.session.execute("SELECT 1")
    except Exception:
        return False
    return True


def load_points() -> Dict[str, Dict[str, int]]:
    if _use_db():
        assert User is not None
        data: Dict[str, Dict[str, int]] = {}
        for u in User.query.all():  # type: ignore[attr-defined]
            data[u.username] = {"A": u.points_a, "O": u.points_o}
        return data
    if POINTS_PATH.exists():
        with open(POINTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def load_points_history() -> List[Dict[str, str]]:
    if _use_db():
        assert PointsHistory is not None
        results: List[Dict[str, str]] = []
        for h in PointsHistory.query.order_by(PointsHistory.id).all():  # type: ignore[attr-defined]
            results.append(
                {
                    "username": h.user.username if h.user else "",
                    "A": h.delta_a,
                    "O": h.delta_o,
                    "timestamp": h.timestamp.isoformat(timespec="seconds"),
                }
            )
        return results
    if POINTS_HISTORY_PATH.exists():
        with open(POINTS_HISTORY_PATH, "r", encoding="utf-8") as f:
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
    ts = timestamp or datetime.now()
    if _use_db():
        assert PointsHistory is not None and User is not None
        user = User.query.filter_by(username=username).first()  # type: ignore[attr-defined]
        if not user:
            user = User(username=username, email=f"{username}@example.com")  # type: ignore[call-arg]
            db.session.add(user)
            db.session.flush()
        history = PointsHistory(
            user_id=user.id,
            delta_a=delta_a,
            delta_o=delta_o,
            timestamp=ts,
        )
        db.session.add(history)
        db.session.commit()
        return
    history = load_points_history()
    history.append(
        {
            "username": username,
            "A": delta_a,
            "O": delta_o,
            "timestamp": ts.isoformat(timespec="seconds"),
        }
    )
    with open(POINTS_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def save_points(points: Dict[str, Dict[str, int]]) -> None:
    if _use_db():
        assert User is not None
        for username, vals in points.items():
            user = User.query.filter_by(username=username).first()  # type: ignore[attr-defined]
            if not user:
                user = User(username=username, email=f"{username}@example.com")  # type: ignore[call-arg]
                db.session.add(user)
            user.points_a = vals.get("A", 0)
            user.points_o = vals.get("O", 0)
        db.session.commit()
        return
    with open(POINTS_PATH, "w", encoding="utf-8") as f:
        json.dump(points, f, ensure_ascii=False, indent=2)


def load_posts() -> List[Dict[str, str]]:
    if _use_db():
        assert Post is not None and User is not None
        results: List[Dict[str, str]] = []
        for p in Post.query.order_by(Post.id).all():  # type: ignore[attr-defined]
            results.append(
                {
                    "id": p.id,
                    "author": p.author.username if p.author else "",
                    "category": p.category,
                    "text": p.text,
                    "timestamp": p.timestamp.isoformat(timespec="seconds"),
                }
            )
        return results
    if POSTS_PATH.exists():
        with open(POSTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_posts(posts: List[Dict[str, str]]) -> None:
    if _use_db():
        assert Post is not None and User is not None
        # Replace existing posts with provided list
        Post.query.delete()  # type: ignore[attr-defined]
        for p in posts:
            author = User.query.filter_by(username=p.get("author")).first()  # type: ignore[attr-defined]
            if not author:
                author = User(username=p.get("author"), email=f"{p.get('author')}@example.com")  # type: ignore[call-arg]
                db.session.add(author)
                db.session.flush()
            db.session.add(
                Post(
                    id=p.get("id"),
                    author_id=author.id,
                    category=p.get("category"),
                    text=p.get("text"),
                    timestamp=datetime.fromisoformat(p.get("timestamp"))
                    if p.get("timestamp")
                    else datetime.utcnow(),
                )
            )
        db.session.commit()
        return
    with open(POSTS_PATH, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)


def add_post(author: str, category: str, text: str) -> None:
    if _use_db():
        assert Post is not None and User is not None
        user = User.query.filter_by(username=author).first()  # type: ignore[attr-defined]
        if not user:
            user = User(username=author, email=f"{author}@example.com")  # type: ignore[call-arg]
            db.session.add(user)
            db.session.flush()
        post = Post(
            author_id=user.id,
            category=category,
            text=text,
            timestamp=datetime.utcnow(),
        )
        db.session.add(post)
        db.session.commit()
        return
    posts = load_posts()
    next_id = max((p.get("id", 0) for p in posts), default=0) + 1
    post = {
        "id": next_id,
        "author": author,
        "category": category,
        "text": text,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }
    posts.append(post)
    save_posts(posts)


def update_post(post_id: int, category: str, text: str) -> bool:
    """Update an existing post.

    Parameters
    ----------
    post_id : int
        ID of the post to update.
    category : str
        New category.
    text : str
        New text body.

    Returns
    -------
    bool
        ``True`` if the post existed and was updated.
    """
    if _use_db():
        assert Post is not None
        post = Post.query.filter_by(id=post_id).first()  # type: ignore[attr-defined]
        if not post:
            return False
        post.category = category
        post.text = text
        db.session.commit()
        return True

    posts = load_posts()
    updated = False
    for p in posts:
        if p.get("id") == post_id:
            p["category"] = category
            p["text"] = text
            updated = True
            break
    if updated:
        save_posts(posts)
    return updated


def delete_post(post_id: int) -> bool:
    if _use_db():
        assert Post is not None
        post = Post.query.filter_by(id=post_id).first()  # type: ignore[attr-defined]
        if not post:
            return False
        db.session.delete(post)
        db.session.commit()
        return True
    posts = load_posts()
    new_posts = [p for p in posts if p.get("id") != post_id]
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
    if _use_db():
        assert Post is not None and User is not None
        query = Post.query  # type: ignore[attr-defined]
        if category:
            query = query.filter_by(category=category)
        if author:
            query = query.join(User).filter(User.username == author)
        if keyword:
            query = query.filter(Post.text.contains(keyword))
        results = []
        for p in query.all():
            results.append(
                {
                    "id": p.id,
                    "author": p.author.username if p.author else "",
                    "category": p.category,
                    "text": p.text,
                    "timestamp": p.timestamp.isoformat(timespec="seconds"),
                }
            )
        return results
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
    if _use_db():
        assert User is not None
        u = User.query.filter_by(username=username).first()  # type: ignore[attr-defined]
        if u and u.password == password:
            return {"username": u.username, "role": u.role, "email": u.email}
        return None
    user = config.USERS.get(username)
    if user and user["password"] == password:
        return {
            "username": username,
            "role": user["role"],
            "email": user["email"],
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
