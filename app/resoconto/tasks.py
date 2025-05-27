# -*- coding: utf-8 -*-
"""Scheduled tasks for resoconto module."""

from typing import List, Tuple, Dict
from datetime import date, timedelta

try:
    from apscheduler.schedulers.background import BackgroundScheduler  # pragma: no cover - optional
except Exception:  # pragma: no cover - optional dependency
    BackgroundScheduler = None  # type: ignore

import config
from app.utils import send_email
from app import utils as post_utils
from app.calendario import utils as calendario_utils
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

    admin_email = utils.get_admin_email()
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

    admin_email = utils.get_admin_email()
    if admin_email:
        send_email("Daily resoconto analysis", body, admin_email)

    return {"ranking": ranking, "analysis": analysis}


def evaluate_daily_reports(target: date = date.today()) -> Dict[str, List[str]]:
    """Select best and worst performers for the given date."""

    reports = res_utils.filter_reports(start=target, end=target)
    scores: Dict[str, int] = {}
    for r in reports:
        author = r.get("author")
        length = sum(len(r.get(k, "").split()) for k in ("work", "issue", "success", "failure"))
        if author:
            scores[author] = scores.get(author, 0) + length
    ordered = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best = [u for u, _ in ordered[:2]]
    worst = [u for u, _ in ordered[-2:]] if len(ordered) >= 2 else []
    res_utils.add_claude_entry({"date": target.isoformat(), "best": best, "worst": worst})
    return {"best": best, "worst": worst}


def evaluate_monthly_reports(target: date = date.today()) -> Dict[str, List[str]]:
    """Select best and worst performers for previous month."""

    first = target.replace(day=1) - timedelta(days=1)
    start = first.replace(day=1)
    end = first
    reports = res_utils.filter_reports(start=start, end=end)
    scores: Dict[str, int] = {}
    for r in reports:
        author = r.get("author")
        length = sum(len(r.get(k, "").split()) for k in ("work", "issue", "success", "failure"))
        if author:
            scores[author] = scores.get(author, 0) + length
    ordered = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best = [u for u, _ in ordered[:2]]
    worst = [u for u, _ in ordered[-2:]] if len(ordered) >= 2 else []
    res_utils.add_claude_entry({"month": start.strftime("%Y-%m"), "best": best, "worst": worst})
    return {"best": best, "worst": worst}


def remind_missing_reports(target: date = date.today() - timedelta(days=1)) -> List[str]:
    """Notify users who had shifts but didn't submit reports."""

    events = calendario_utils.load_events()
    scheduled = {e.get("employee") for e in events if e.get("date") == target.isoformat()}
    reports = res_utils.filter_reports(start=target, end=target)
    submitted = {r.get("author") for r in reports}
    missing = scheduled - submitted
    notified = []
    for name in missing:
        email = config.USERS.get(name, {}).get("email")
        if email:
            send_email("Resoconto reminder", "Please submit yesterday's report", email)
            notified.append(name)
    return notified


def start_scheduler() -> None:
    """Start APScheduler to run the daily job at 4 AM."""

    if scheduler is None:
        return

    if not scheduler.get_jobs():
        scheduler.add_job(lambda: daily_post_job(), "cron", hour=4)
        scheduler.add_job(lambda: daily_report_job(), "cron", hour=4, minute=5)
        scheduler.add_job(lambda: evaluate_daily_reports(date.today()), "cron", hour=4, minute=10)
        scheduler.add_job(lambda: evaluate_monthly_reports(date.today()), "cron", hour=4, minute=15)
        scheduler.add_job(lambda: remind_missing_reports(), "cron", hour="1-5")
        scheduler.start()


