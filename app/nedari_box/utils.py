import json
from pathlib import Path
from datetime import datetime

import config

NEDARI_PATH = Path(getattr(config, 'NEDARI_FILE', 'nedari.json'))


def load_posts():
    if NEDARI_PATH.exists():
        with open(NEDARI_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_posts(posts):
    with open(NEDARI_PATH, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)


def add_post(author, body, targets, visibility):
    posts = load_posts()
    next_id = max((p.get('id', 0) for p in posts), default=0) + 1
    posts.append({
        'id': next_id,
        'author': author,
        'body': body,
        'targets': targets,
        'visibility': visibility,
        'timestamp': datetime.now().isoformat(timespec='seconds'),
    })
    save_posts(posts)
