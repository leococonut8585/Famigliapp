# -*- coding: utf-8 -*-
"""Scheduled tasks for resoconto module."""

from typing import List, Tuple, Dict

try:
    from apscheduler.schedulers.background import BackgroundScheduler  # pragma: no cover - optional
except Exception:  # pragma: no cover - optional dependency
    BackgroundScheduler = None  # type: ignore

import config
from app.utils import send_email
from app import utils as post_utils
from . import utils as res_utils


scheduler = BackgroundScheduler() if BackgroundScheduler else None  # type: ignore


def collect_post_stats() -> Tuple[List[Tuple[str, int]], Dict[str, int]]:
    """Aggregate post statistics.

    Returns
    -------
    Tuple[List[Tuple[str, int]], Dict[str, int]]
        Ranking list of (author, count) and analysis summary.
    """

    posts = post_utils.load_posts()
    ranking_dict: Dict[str, int] = {}
    category_count: Dict[str, int] = {}
    for p in posts:
        author = p.get("author")
        if author:
            ranking_dict[author] = ranking_dict.get(author, 0) + 1
        cat = p.get("category")
        if cat:
            category_count[cat] = category_count.get(cat, 0) + 1

    ranking = sorted(ranking_dict.items(), key=lambda x: x[1], reverse=True)
    top_category = max(category_count.items(), key=lambda x: x[1])[0] if category_count else ""
    summary = {
        "total_posts": len(posts),
        "top_category": top_category,
    }
    return ranking, summary


def daily_post_job() -> Dict[str, object]:
    """Job executed daily to summarize posts and notify admin."""

    ranking, summary = collect_post_stats()
    lines = ["Post ranking:"]
    for user, cnt in ranking:
        lines.append(f"{user}: {cnt}")
    if summary.get("top_category"):
        lines.append(f"Top category: {summary['top_category']}")
    lines.append(f"Total posts: {summary['total_posts']}")
    body = "\n".join(lines)

    admin_email = config.USERS.get("admin", {}).get("email")
    if admin_email:
        send_email("Daily post summary", body, admin_email)

    return {"ranking": ranking, "summary": summary}


def analyze_reports() -> Tuple[List[Tuple[str, int]], Dict[str, str]]:
    """簡易的にレソコント内容を解析してランキングとコメントを返す。"""

    reports = res_utils.load_reports()
    word_counts: Dict[str, int] = {}
    for r in reports:
        author = r.get("author")
        body = r.get("body", "")
        if author:
            word_counts[author] = word_counts.get(author, 0) + len(body.split())

    ranking = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)

    analysis: Dict[str, str] = {}
    for user, count in word_counts.items():
        analysis[user] = "詳細な報告です" if count > 20 else "簡潔な報告です"

    return ranking, analysis


def daily_report_job() -> Dict[str, object]:
    """業務報告を集計し管理者へ送信するジョブ。"""

    ranking, analysis = analyze_reports()
    lines = ["Resoconto analysis:"]
    for user, cnt in ranking:
        comment = analysis.get(user, "")
        lines.append(f"{user}: {cnt} words - {comment}")
    body = "\n".join(lines)

    admin_email = config.USERS.get("admin", {}).get("email")
    if admin_email:
        send_email("Daily resoconto analysis", body, admin_email)

    return {"ranking": ranking, "analysis": analysis}


def start_scheduler() -> None:
    """Start APScheduler to run the daily job at 4 AM."""

    if scheduler is None:
        return

    if not scheduler.get_jobs():
        scheduler.add_job(lambda: daily_post_job(), "cron", hour=4)
        scheduler.add_job(lambda: daily_report_job(), "cron", hour=4, minute=5)
        scheduler.start()

