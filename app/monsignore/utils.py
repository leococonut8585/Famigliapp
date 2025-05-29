"""Utility functions for Monsignore posts and Kadai features."""

import json
from datetime import datetime, timedelta # Added timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any # Added List, Dict, Optional, Any

import config

# --- Settings for Original Monsignore Posts ---
POST_ALLOWED_EXTS = {"png", "jpg", "jpeg", "gif"} # Renamed for clarity
MAX_POST_FILE_SIZE = 10 * 1024 * 1024 # 10MB, Renamed for clarity
MONSIGNORE_PATH = Path(getattr(config, "MONSIGNORE_FILE", "monsignore.json"))

# --- Settings for New Kadai Feature ---
KADAI_ALLOWED_EXTS = {"png", "jpg", "jpeg", "gif", "mp4", "mov", "avi", "wmv", "mkv"}
MAX_KADAI_FILE_SIZE = 3 * 1024 * 1024 * 1024 # 3GB
KADAI_PATH = Path(getattr(config, "MONSIGNORE_KADAI_FILE", "monsignore_kadai.json"))


# --- Original Monsignore Post Functions ---

def load_posts() -> List[Dict[str, Any]]: # Updated type hint
    if MONSIGNORE_PATH.exists():
        with open(MONSIGNORE_PATH, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return [] # Return empty list if JSON is invalid
    return []


def save_posts(posts: List[Dict[str, Any]]) -> None: # Updated type hint
    with open(MONSIGNORE_PATH, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)


def add_post(author: str, body: str, filename: Optional[str] = None) -> None: # Updated type hints
    posts = load_posts()
    next_id = max((p.get("id", 0) for p in posts), default=0) + 1
    posts.append(
        {
            "id": next_id,
            "author": author,
            "body": body,
            "filename": filename,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
    )
    save_posts(posts)


def delete_post(post_id: int) -> bool: # Updated type hint
    posts = load_posts()
    new_posts = [p for p in posts if p.get("id") != post_id]
    if len(new_posts) == len(posts):
        return False
    save_posts(new_posts)
    return True


def filter_posts(author: str = "", keyword: str = "") -> List[Dict[str, Any]]: # Updated type hints
    posts = load_posts()
    results = []
    for p in posts:
        if author and p.get("author") != author:
            continue
        if keyword and keyword.lower() not in p.get("body", "").lower():
            continue
        results.append(p)
    return results

# --- New Kadai Feature Functions ---

def load_kadai_entries() -> List[Dict[str, Any]]:
    """Loads and returns entries from KADAI_PATH."""
    if KADAI_PATH.exists():
        with open(KADAI_PATH, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return [] # Return empty list if JSON is invalid
    return []


def save_kadai_entries(entries: List[Dict[str, Any]]) -> None:
    """Saves the given list of entries to KADAI_PATH."""
    with open(KADAI_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def add_kadai_entry(
    author: str,
    title: str,
    text_body: Optional[str],
    filename: Optional[str],
    file_type: Optional[str],
    original_filename: Optional[str]
) -> int:
    """Adds a new Kadai entry and returns its ID."""
    entries = load_kadai_entries()
    next_id = max((int(e.get("id", 0)) for e in entries), default=0) + 1
    
    new_entry = {
        "id": next_id,
        "author": author,
        "title": title,
        "text_body": text_body,
        "filename": filename,
        "file_type": file_type,
        "original_filename": original_filename,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "feedback_deadline": (datetime.now() + timedelta(hours=48)).isoformat(timespec="seconds"),
        "status": "active",  # "active" or "archived"
        "feedback_submissions": {}, # {username: {"text": "...", "timestamp": "..."}}
        "overdue_admin_notified_users": [] # List of usernames (admins) notified
    }
    entries.append(new_entry)
    save_kadai_entries(entries)
    return next_id


def get_kadai_entry_by_id(entry_id: int) -> Optional[Dict[str, Any]]:
    """Loads entries, returns the one matching entry_id, or None."""
    entries = load_kadai_entries()
    for entry in entries:
        if entry.get("id") == entry_id:
            return entry
    return None


def get_active_kadai_entries() -> List[Dict[str, Any]]:
    """Loads entries, returns those where status == "active"."""
    entries = load_kadai_entries()
    return [entry for entry in entries if entry.get("status") == "active"]


def get_archived_kadai_entries() -> List[Dict[str, Any]]:
    """Loads entries, returns those where status == "archived"."""
    entries = load_kadai_entries()
    return [entry for entry in entries if entry.get("status") == "archived"]


def archive_kadai_entry(entry_id: int) -> bool:
    """Loads entries, finds by ID, sets status = "archived". Saves and returns True if successful."""
    entries = load_kadai_entries()
    entry_found = False
    for entry in entries:
        if entry.get("id") == entry_id:
            entry["status"] = "archived"
            entry_found = True
            break
    if entry_found:
        save_kadai_entries(entries)
        return True
    return False


def delete_kadai_entry(entry_id: int) -> bool:
    """Deletes a Kadai entry by its ID. Returns True if successful, False otherwise."""
    entries = load_kadai_entries()
    original_length = len(entries)
    new_entries = [entry for entry in entries if entry.get("id") != entry_id]
    
    if len(new_entries) < original_length:
        # Also consider deleting the associated file if it exists
        # For now, just removing the entry from JSON
        # To implement file deletion:
        # for entry in entries:
        #     if entry.get("id") == entry_id:
        #         if entry.get("filename"):
        #             try:
        #                 file_path = Path(config.UPLOAD_FOLDER) / entry["filename"]
        #                 file_path.unlink(missing_ok=True)
        #             except Exception as e:
        #                 # Log the error, e.g., print(f"Error deleting file {entry['filename']}: {e}")
        #                 pass # Decide if failure to delete file should prevent entry deletion
        #         break
        save_kadai_entries(new_entries)
        return True
    return False


def add_feedback_to_kadai(entry_id: int, username: str, feedback_text: str) -> bool:
    """Adds/updates feedback for a Kadai entry."""
    entries = load_kadai_entries()
    entry_updated = False
    for entry in entries:
        if entry.get("id") == entry_id:
            if entry.get("status") == "active": # Can only add feedback to active kadai
                if "feedback_submissions" not in entry: # Ensure field exists
                    entry["feedback_submissions"] = {}
                entry["feedback_submissions"][username] = {
                    "text": feedback_text,
                    "timestamp": datetime.now().isoformat(timespec="seconds")
                }
                entry_updated = True
            break 
            
    if entry_updated:
        save_kadai_entries(entries)
        return True
    return False


def add_user_to_kadai_admin_notified_list(entry_id: int, username: str) -> bool:
    """Adds a username to the list of admins notified about overdue feedback for a Kadai entry."""
    entries = load_kadai_entries()
    user_added = False
    entry_found = False
    for entry in entries:
        if entry.get("id") == entry_id:
            entry_found = True
            # Ensure the list exists, using setdefault to initialize if not present
            notified_list = entry.setdefault("overdue_admin_notified_users", [])
            if username not in notified_list:
                notified_list.append(username)
                user_added = True
            break

    if entry_found and user_added: # Only save if user was actually added
        save_kadai_entries(entries)
        return True
    return False
