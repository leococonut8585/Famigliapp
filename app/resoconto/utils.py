import json
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Tuple, Dict

import config

REPORTS_PATH = Path(getattr(config, "RESOCONTO_FILE", "resoconto.json"))


def load_reports():
    if REPORTS_PATH.exists():
        with open(REPORTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_reports(reports):
    with open(REPORTS_PATH, "w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False, indent=2)


def add_report(author: str, report_date: date, body: str) -> None:
    reports = load_reports()
    next_id = max((r.get("id", 0) for r in reports), default=0) + 1
    reports.append(
        {
            "id": next_id,
            "author": author,
            "date": report_date.isoformat(),
            "body": body,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
    )
    save_reports(reports)


def delete_report(report_id: int) -> bool:
    reports = load_reports()
    new_reports = [r for r in reports if r.get("id") != report_id]
    if len(new_reports) == len(reports):
        return False
    save_reports(new_reports)
    return True


def get_ranking(start: Optional[date] = None, end: Optional[date] = None) -> List[Tuple[str, int]]:
    """指定期間内のユーザー別報告数ランキングを返す。"""

    reports = load_reports()
    counts: Dict[str, int] = {}
    for r in reports:
        d_str = r.get("date")
        try:
            d = date.fromisoformat(d_str) if d_str else None
        except ValueError:
            d = None
        if start and d and d < start:
            continue
        if end and d and d > end:
            continue
        user = r.get("author")
        if user:
            counts[user] = counts.get(user, 0) + 1

    return sorted(counts.items(), key=lambda x: x[1], reverse=True)
