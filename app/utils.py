import csv
import json
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage

try:
    from flask_mail import Message
except Exception:  # pragma: no cover - optional dependency
    Message = None  # type: ignore

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
COMMENTS_PATH = Path(getattr(config, "COMMENTS_FILE", "comments.json"))


def send_email(subject: str, body: str, to: str) -> None:
    """Send an email using Flask-Mail if available, otherwise smtplib."""

    if current_app is not None and Message is not None and "mail" in current_app.extensions:
        msg = Message(
            subject=subject,
            recipients=[to],
            body=body,
            sender=getattr(current_app.config, "MAIL_SENDER", "famigliapp@example.com"),
        )
        current_app.extensions["mail"].send(msg)
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = getattr(config, "MAIL_SENDER", "famigliapp@example.com")
    msg["To"] = to
    msg.set_content(body)
    with smtplib.SMTP(getattr(config, "MAIL_SERVER", "localhost"), getattr(config, "MAIL_PORT", 25)) as smtp:
        smtp.send_message(msg)


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


def log_points_change(
    username: str, delta_a: int, delta_o: int, timestamp: Optional[datetime] = None
) -> None:
    """Record a change in points and send a notification email."""

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
    else:
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

    email = config.USERS.get(username, {}).get("email")
    if email:
        body = f"A: {delta_a}  O: {delta_o}"
        send_email("Points updated", body, email)


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


def add_post(author: str, category: str, text: str, filename: Optional[str] = None) -> None:
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
    if filename:
        post["filename"] = filename
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
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
) -> List[Dict[str, str]]:
    """Filter posts by category, author, keyword and date range."""
    if _use_db():
        assert Post is not None and User is not None
        query = Post.query  # type: ignore[attr-defined]
        if category:
            query = query.filter_by(category=category)
        if author:
            query = query.join(User).filter(User.username == author)
        if keyword:
            query = query.filter(Post.text.ilike(f"%{keyword}%"))
        if start:
            query = query.filter(Post.timestamp >= start)
        if end:
            query = query.filter(Post.timestamp <= end)
        results = []
        for p in query.all():
            results.append(
                {
                    "id": p.id,
                    "author": p.author.username if p.author else "",
                    "category": p.category,
                    "text": p.text,
                    "timestamp": p.timestamp.isoformat(timespec="seconds"),
                    "filename": None,
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
        if keyword and keyword.lower() not in p.get("text", "").lower():
            continue
        if start or end:
            try:
                ts = datetime.fromisoformat(p.get("timestamp"))
            except Exception:
                continue
            if start and ts < start:
                continue
            if end and ts > end:
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


def export_points_history_csv(path: str) -> None:
    """ポイント履歴をCSVファイルに出力する。"""

    history = load_points_history()
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "username", "A", "O"])
        for entry in history:
            writer.writerow(
                [
                    entry.get("timestamp", ""),
                    entry.get("username", ""),
                    entry.get("A", 0),
                    entry.get("O", 0),
                ]
            )


def get_points_history_summary(
    start: Optional[datetime] = None, end: Optional[datetime] = None
) -> Dict[str, List[int]]:
    """Return aggregated points history for graphing.

    The result contains ``labels`` (date strings), ``A`` values and ``O`` values
    for each date within the range.
    """

    history = filter_points_history(start=start, end=end)
    data: Dict[str, Dict[str, int]] = {}
    for entry in history:
        date_str = datetime.fromisoformat(entry.get("timestamp")).date().isoformat()
        if date_str not in data:
            data[date_str] = {"A": 0, "O": 0}
        data[date_str]["A"] += entry.get("A", 0)
        data[date_str]["O"] += entry.get("O", 0)

    labels = sorted(data.keys())
    a_values = [data[d]["A"] for d in labels]
    o_values = [data[d]["O"] for d in labels]

    return {"labels": labels, "A": a_values, "O": o_values}


def get_growth_ranking(metric: str = "U", period: str = "weekly") -> List[Tuple[str, float]]:
    """Return ranking based on growth rate of the specified metric.

    The growth rate is calculated by comparing the total gain in the current
    period with that of the previous period. If the previous period total is
    zero, the rate is treated as infinite when the current total is positive.
    """

    metric = metric.upper()
    period = period.lower()

    if period == "weekly":
        days = 7
    elif period == "monthly":
        days = 30
    elif period == "yearly":
        days = 365
    else:  # pragma: no cover - invalid period
        raise ValueError("invalid period")

    end = datetime.now()
    start = end - timedelta(days=days)
    prev_start = start - timedelta(days=days)
    prev_end = start - timedelta(seconds=1)

    current = filter_points_history(start=start, end=end)
    previous = filter_points_history(start=prev_start, end=prev_end)

    def accumulate(entries: List[Dict[str, str]]) -> Dict[str, int]:
        data: Dict[str, int] = {}
        for e in entries:
            val = 0
            if metric == "U":
                val = e.get("A", 0) - e.get("O", 0)
            else:
                val = e.get(metric, 0)
            user = e.get("username")
            data[user] = data.get(user, 0) + val
        return data

    current_totals = accumulate(current)
    prev_totals = accumulate(previous)

    ranking: List[Tuple[str, float]] = []
    for user, cur in current_totals.items():
        prev = prev_totals.get(user, 0)
        if prev == 0:
            rate = float("inf") if cur > 0 else 0.0
        else:
            rate = (cur - prev) / abs(prev)
        ranking.append((user, rate))

    ranking.sort(key=lambda x: x[1], reverse=True)
    return ranking


def load_comments() -> List[Dict[str, str]]:
    """Load comments from storage."""
    if COMMENTS_PATH.exists():
        with open(COMMENTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_comments(comments: List[Dict[str, str]]) -> None:
    """Save comments list."""
    with open(COMMENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)


def add_comment(post_id: int, author: str, text: str) -> None:
    """Add a comment to the specified post."""
    comments = load_comments()
    comments.append(
        {
            "post_id": post_id,
            "author": author,
            "text": text,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
    )
    save_comments(comments)


def get_comments(post_id: int) -> List[Dict[str, str]]:
    """Return comments for a given post."""
    return [c for c in load_comments() if c.get("post_id") == post_id]
