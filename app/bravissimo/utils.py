"""Utility functions for Bravissimo posts."""

from typing import List, Dict, Optional

from app import utils as post_utils


def filter_posts(author: str = "", keyword: str = "") -> List[Dict[str, str]]:
    """Return posts from the generic posts storage filtered for Bravissimo."""
    return post_utils.filter_posts(
        category="bravissimo", author=author, keyword=keyword
    )


def add_post(author: str, body: str, filename: Optional[str] = None) -> None:
    post_utils.add_post(author, "bravissimo", body, filename)


def delete_post(post_id: int) -> bool:
    return post_utils.delete_post(post_id)
