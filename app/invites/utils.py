"""Utility functions for invite codes."""

import json
import uuid
from pathlib import Path
from datetime import datetime

import config

INVITES_PATH = Path(getattr(config, "INVITES_FILE", "invites.json"))


def load_invites():
    if INVITES_PATH.exists():
        with open(INVITES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_invites(invites):
    with open(INVITES_PATH, "w", encoding="utf-8") as f:
        json.dump(invites, f, ensure_ascii=False, indent=2)


def create_invite() -> str:
    invites = load_invites()
    code = uuid.uuid4().hex[:8]
    invites.append({"code": code, "created": datetime.now().isoformat(timespec="seconds"), "used_by": ""})
    save_invites(invites)
    return code


def delete_invite(code: str) -> bool:
    invites = load_invites()
    new_invites = [i for i in invites if i.get("code") != code]
    if len(new_invites) == len(invites):
        return False
    save_invites(new_invites)
    return True


def mark_used(code: str, username: str) -> bool:
    invites = load_invites()
    for i in invites:
        if i.get("code") == code and not i.get("used_by"):
            i["used_by"] = username
            save_invites(invites)
            return True
    return False
