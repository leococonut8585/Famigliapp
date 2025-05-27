"""Utility functions for Bravissimo posts."""

from typing import List, Dict, Optional
import io
import os
import wave

from app import utils as post_utils
import config
from app.utils import send_email

MAX_AUDIO_DURATION = 20 * 60  # 20 minutes in seconds


def filter_posts(author: str = "", keyword: str = "", target: str = "") -> List[Dict[str, str]]:
    """Return posts from the generic posts storage filtered for Bravissimo."""
    posts = post_utils.filter_posts(
        category="bravissimo", author=author, keyword=keyword
    )
    if target:
        posts = [p for p in posts if p.get("target") == target]
    return posts


def add_post(author: str, filename: Optional[str] = None, target: str = "") -> None:
    """Add a new Bravissimo post with optional audio file."""

    post_utils.add_post(author, "bravissimo", "", filename, extra={"target": target})
    if target:
        email = config.USERS.get(target, {}).get("email")
        if email:
            send_email("Bravissimo!", "", email)


def delete_post(post_id: int) -> bool:
    return post_utils.delete_post(post_id)


def validate_audio(fs) -> None:
    """Validate uploaded audio duration (wav only)."""

    if not fs or not fs.filename:
        raise ValueError("ファイルが指定されていません")
    ext = os.path.splitext(fs.filename)[1].lower()
    if ext == ".wav":
        data = fs.read()
        fs.stream.seek(0)
        try:
            with wave.open(io.BytesIO(data)) as wf:
                duration = wf.getnframes() / float(wf.getframerate())
        except Exception:
            raise ValueError("音声ファイルを読み取れません")
        if duration > MAX_AUDIO_DURATION:
            raise ValueError("20分を超える音声はアップロードできません")
