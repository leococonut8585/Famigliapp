import csv
import json
from pathlib import Path
from typing import Dict, Optional, List, Tuple, Set
import uuid
import shutil
import re
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage
import urllib.request
import urllib.parse
import os

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
POINTS_CONSUMPTION_PATH = Path(
    getattr(config, "POINTS_CONSUMPTION_FILE", "points_consumption.json")
)
POSTS_PATH = Path(config.POSTS_FILE)
COMMENTS_PATH = Path(getattr(config, "COMMENTS_FILE", "comments.json"))

# File upload settings
ALLOWED_EXTENSIONS = {
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
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10MB


def allowed_file(filename: str) -> bool:
    """Return True if the filename has an allowed extension."""

    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def file_size(fs) -> int:
    """Return file size for a Werkzeug ``FileStorage`` object."""

    pos = fs.stream.tell()
    fs.stream.seek(0, os.SEEK_END)
    size = fs.stream.tell()
    fs.stream.seek(pos)
    return size


_filename_strip_re = re.compile(r"[^A-Za-z0-9_.-]")


def secure_filename(name: str) -> str:
    """A simplified version of Werkzeug's ``secure_filename``."""

    name = os.path.basename(name)
    name = name.replace(" ", "_")
    name = _filename_strip_re.sub("", name)
    return name[:100]


def save_uploaded_file(
    fs,
    upload_folder: str,
    allowed_exts: Optional[Set[str]] = None,
    max_size: int = MAX_ATTACHMENT_SIZE,
) -> str:
    """Validate and save an uploaded ``FileStorage`` object.

    Parameters
    ----------
    fs : FileStorage
        Uploaded file object.
    upload_folder : str
        Destination directory.

    Returns
    -------
    str
        Saved file name (without path).

    Raises
    ------
    ValueError
        If file type is not allowed or size exceeds the limit.
    """

    if not fs or not fs.filename:
        raise ValueError("ファイルが指定されていません")
    ext_ok = allowed_file(fs.filename) if allowed_exts is None else (
        "." in fs.filename
        and fs.filename.rsplit(".", 1)[1].lower() in allowed_exts
    )
    if not ext_ok:
        raise ValueError("許可されていないファイル形式です")
    if file_size(fs) > max_size:
        raise ValueError("ファイルサイズが大きすぎます")

    os.makedirs(upload_folder, exist_ok=True)
    filename = secure_filename(fs.filename)
    unique = uuid.uuid4().hex
    filename = f"{unique}_{filename}"
    fs.save(os.path.join(upload_folder, filename))
    return filename


def save_local_file(
    path: str,
    upload_folder: str,
    allowed_exts: Optional[Set[str]] = None,
    max_size: int = MAX_ATTACHMENT_SIZE,
) -> str:
    """Validate and copy a local file into ``upload_folder``.

    Parameters
    ----------
    path : str
        Source file path.
    upload_folder : str
        Destination directory.

    Returns
    -------
    str
        Saved file name.
    """

    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    ext_ok = allowed_file(path) if allowed_exts is None else (
        "." in path and path.rsplit(".", 1)[1].lower() in allowed_exts
    )
    if not ext_ok:
        raise ValueError("許可されていないファイル形式です")
    if os.path.getsize(path) > max_size:
        raise ValueError("ファイルサイズが大きすぎます")

    os.makedirs(upload_folder, exist_ok=True)
    filename = secure_filename(os.path.basename(path))
    unique = uuid.uuid4().hex
    dest = os.path.join(upload_folder, f"{unique}_{filename}")
    shutil.copy(path, dest)
    return os.path.basename(dest)


def send_email(subject: str, body: str, to: str) -> None:
    """Send an email using Flask-Mail if available, otherwise smtplib."""

    try:
        if current_app is not None and Message is not None and "mail" in current_app.extensions:
            msg = Message(
                subject=subject,
                recipients=[to],
                body=body,
                sender=getattr(current_app.config, "MAIL_SENDER", "famigliapp@example.com"),
            )
            current_app.extensions["mail"].send(msg)
        else: # Fallback to smtplib
            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = getattr(config, "MAIL_SENDER", "famigliapp@example.com")
            msg["To"] = to
            msg.set_content(body)
            # Ensure MAIL_SERVER and MAIL_PORT are defined in config or have defaults
            mail_server = getattr(config, "MAIL_SERVER", "localhost")
            mail_port = getattr(config, "MAIL_PORT", 25)
            with smtplib.SMTP(mail_server, mail_port) as smtp:
                # Add STARTTLS if supported by the server and configured
                if getattr(config, "MAIL_USE_TLS", False): # Assuming a MAIL_USE_TLS config option
                    smtp.starttls()
                # Add login if username/password are configured
                mail_username = getattr(config, "MAIL_USERNAME", None)
                mail_password = getattr(config, "MAIL_PASSWORD", None)
                if mail_username and mail_password:
                    smtp.login(mail_username, mail_password)
                smtp.send_message(msg)
    except Exception as exc:
        log_message = f"Failed to send email (suppressed): {exc}"
        if current_app:
            current_app.logger.warning(log_message)
        else:
            print(log_message) # Print to console if no Flask app context

    # These notifications will still be attempted even if email fails
    send_line_notify(f"{subject}\n{body}")
    send_pushbullet_notify(subject, body)


def send_line_notify(message: str) -> None:
    """Send notification via LINE Notify if token is configured."""

    token = getattr(config, "LINE_NOTIFY_TOKEN", "")
    if not token:
        return
    data = urllib.parse.urlencode({"message": message}).encode()
    req = urllib.request.Request(
        "https://notify-api.line.me/api/notify",
        data=data,
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10):  # pragma: no cover - network
            pass
    except Exception:
        pass


def send_pushbullet_notify(title: str, body: str) -> None:
    """Send notification via Pushbullet if token is configured."""

    token = getattr(config, "PUSHBULLET_TOKEN", "")
    if not token:
        return
    data = json.dumps({"type": "note", "title": title, "body": body}).encode()
    req = urllib.request.Request(
        "https://api.pushbullet.com/v2/pushes",
        data=data,
        headers={"Access-Token": token, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10):  # pragma: no cover - network
            pass
    except Exception:
        pass


def get_admin_email() -> Optional[str]:
    """Return the email address of the first admin user if available."""

    for info in config.USERS.values():
        if info.get("role") == "admin" and info.get("email"):
            return info["email"]
    return None


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


def add_post(
    author: str,
    category: str,
    text: str,
    filename: Optional[str] = None,
    extra: Optional[Dict[str, str]] = None,
) -> None:
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
    if extra:
        post.update(extra)
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


def add_user(username: str, password: str, email: str, role: str = "user") -> None:
    """Add a user to the in-memory user store."""

    config.USERS[username] = {"password": password, "role": role, "email": email}


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
        ranking = [r for r in ranking if config.USERS.get(r[0], {}).get("role") != "admin"]
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
        ranking = [r for r in ranking if config.USERS.get(r[0], {}).get("role") != "admin"]
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


def load_points_consumption() -> List[Dict[str, str]]:
    """Load simple points consumption history."""

    if POINTS_CONSUMPTION_PATH.exists():
        with open(POINTS_CONSUMPTION_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def add_points_consumption(
    username: str, reason: str, timestamp: Optional[datetime] = None
) -> None:
    """Add a points consumption entry."""

    ts = timestamp or datetime.now()
    history = load_points_consumption()
    history.append(
        {
            "username": username,
            "reason": reason,
            "timestamp": ts.isoformat(timespec="seconds"),
        }
    )
    with open(POINTS_CONSUMPTION_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def export_points_consumption_csv(path: str) -> None:
    """Export points consumption history to CSV."""

    history = load_points_consumption()
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "username", "reason"])
        for entry in history:
            writer.writerow(
                [
                    entry.get("timestamp", ""),
                    entry.get("username", ""),
                    entry.get("reason", ""),
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
    if not COMMENTS_PATH.exists():
        return []

    with open(COMMENTS_PATH, "r", encoding="utf-8") as f:
        comments = json.load(f)

    # ensure id field exists
    changed = False
    next_id = max((c.get("id", 0) for c in comments), default=0) + 1
    for c in comments:
        if "id" not in c:
            c["id"] = next_id
            next_id += 1
            changed = True
    if changed:
        save_comments(comments)
    return comments


def save_comments(comments: List[Dict[str, str]]) -> None:
    """Save comments list."""
    with open(COMMENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)


def add_comment(post_id: int, author: str, text: str) -> None:
    """Add a comment to the specified post.

    新規コメントを保存する際に一意な ``id`` を振っておく。既存コメント
    ファイルには ``id`` フィールドが無い場合もあるため、最大値から
    採番する形で互換性を保つ。
    """

    comments = load_comments()
    next_id = max((c.get("id", 0) for c in comments), default=0) + 1
    comments.append(
        {
            "id": next_id,
            "post_id": post_id,
            "author": author,
            "text": text,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
    )
    save_comments(comments)


def update_comment(comment_id: int, text: str) -> bool:
    """Update an existing comment text.

    Parameters
    ----------
    comment_id : int
        ID of the comment to update.
    text : str
        New comment body.

    Returns
    -------
    bool
        ``True`` if the comment existed and was updated.
    """

    comments = load_comments()
    updated = False
    for c in comments:
        if c.get("id") == comment_id:
            c["text"] = text
            updated = True
            break
    if updated:
        save_comments(comments)
    return updated


def get_comments(post_id: int) -> List[Dict[str, str]]:
    """Return comments for a given post.

    旧形式で ``id`` が保存されていないコメントが存在する場合は、ここで
    採番して返す。ファイル自体は更新しないが、表示時に ID が無いことに
    よるエラーを防ぐ。
    """

    results = []
    next_id = 1
    for c in load_comments():
        if c.get("post_id") != post_id:
            continue
        if "id" not in c:
            c = c.copy()
            c["id"] = next_id
            next_id += 1
        results.append(c)
    return results
