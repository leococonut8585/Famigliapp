"""Utility functions for vote box."""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

import config
from app.utils import send_email

VOTE_BOX_PATH = Path(getattr(config, 'VOTE_BOX_FILE', 'votebox.json'))


def load_polls() -> List[Dict]:
    if VOTE_BOX_PATH.exists():
        with open(VOTE_BOX_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_polls(polls: List[Dict]) -> None:
    with open(VOTE_BOX_PATH, 'w', encoding='utf-8') as f:
        json.dump(polls, f, ensure_ascii=False, indent=2)


def add_poll(author: str, title: str, options: List[str], targets: List[str]) -> None:
    polls = load_polls()
    next_id = max((p.get('id', 0) for p in polls), default=0) + 1
    polls.append({
        'id': next_id,
        'author': author,
        'title': title,
        'options': options,
        'votes': {},
        'targets': targets,
        'status': 'open',
        'timestamp': datetime.now().isoformat(timespec='seconds'),
    })
    save_polls(polls)

    for t in targets:
        info = config.USERS.get(t)
        if info and info.get('email'):
            send_email('New Poll', title, info['email'])


def add_vote(poll_id: int, username: str, choice_index: int) -> bool:
    polls = load_polls()
    for p in polls:
        if p.get('id') == poll_id and p.get('status') == 'open':
            p.setdefault('votes', {})[username] = choice_index
            save_polls(polls)
            return True
    return False


def close_poll(poll_id: int) -> bool:
    polls = load_polls()
    for p in polls:
        if p.get('id') == poll_id and p.get('status') == 'open':
            p['status'] = 'closed'
            save_polls(polls)
            return True
    return False
