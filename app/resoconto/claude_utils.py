import json
import os
import urllib.request
from datetime import date, timedelta
from typing import List, Dict

MODEL = "claude-opus-4-20250514"
API_URL = "https://api.anthropic.com/v1/messages"


def _api_key() -> str:
    return os.getenv("CLAUDE_API_KEY") or os.getenv("ANTHROPIC_API_KEY", "")


def call_claude(prompt: str) -> str:
    """Send prompt to Claude API and return the text reply.

    If the API key is not configured or any error occurs, a simple fallback
    string is returned so that the application continues to work offline.
    """
    key = _api_key()
    if not key:
        return "(Claude API key not configured)"
    data = json.dumps({
        "model": MODEL,
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as res:  # pragma: no cover - network
            payload = json.load(res)
        content = payload.get("content")
        if isinstance(content, list) and content:
            return content[0].get("text", "")
        return str(content)
    except Exception as exc:  # pragma: no cover - allow offline
        return f"(Claude API error: {exc})"


def summarize_report(user: str, report: Dict[str, str], history: List[Dict[str, str]]) -> str:
    """Create a prompt from report and history and get Claude's summary."""

    lines = ["あなたは社員の業務報告を要約しアドバイスを与えるAIです。", "過去30日間の報告:"]
    for r in history:
        w = r.get("work", "")
        issue = r.get("issue", "")
        success = r.get("success", "")
        failure = r.get("failure", "")
        lines.append(f"- {w} / {issue} / {success} / {failure}")

    lines.append("今日の報告:")
    lines.append(f"業務内容: {report.get('work','')}")
    lines.append(f"感じた課題: {report.get('issue','')}")
    lines.append(f"うまくいったこと: {report.get('success','')}")
    lines.append(f"失敗したこと: {report.get('failure','')}")
    lines.append("総評を日本語でお願いします。")
    prompt = "\n".join(lines)
    return call_claude(prompt)

