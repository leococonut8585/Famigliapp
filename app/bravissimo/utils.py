"""Utility functions for Bravissimo posts."""

from typing import List, Dict, Optional

from app import utils as post_utils
import config
from app.utils import send_email


def filter_posts(author: str = "", keyword: str = "", target: str = "") -> List[Dict[str, str]]:
    """Return posts from the generic posts storage filtered for Bravissimo."""
    posts = post_utils.filter_posts(
        category="bravissimo", author=author, keyword=keyword
    )
    if target:
        posts = [p for p in posts if p.get("target") == target]
    return posts


def add_post(author: str, body: str, filename: Optional[str] = None, target: str = "") -> None:
    post_utils.add_post(author, "bravissimo", body, filename, extra={"target": target})
    if target:
        email = config.USERS.get(target, {}).get("email")
        if email:
            send_email("Bravissimo!", body, email)


def delete_post(post_id: int) -> bool:
    return post_utils.delete_post(post_id)
