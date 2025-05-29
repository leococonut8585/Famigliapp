"""Utility functions for Decima Reports and Media."""

from datetime import datetime
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple # Added Tuple
import os
import re # For folder name validation

import config

# --- Settings for Decima Reports (Text-based) ---
PRINCIPESSINA_PATH = Path(
    getattr(config, "PRINCIPESSINA_FILE", "principessina.json")
)

# --- Settings for Decima Media (Video/Photo) ---
MEDIA_PATH = Path(
    getattr(config, "PRINCIPESSINA_MEDIA_FILE", "principessina_media.json")
)
ALLOWED_VIDEO_EXTS = {'mp4', 'mov', 'avi', 'wmv', 'mkv', 'webm'}
ALLOWED_PHOTO_EXTS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
MAX_MEDIA_SIZE = 3 * 1024 * 1024 * 1024 # 3GB

# --- Decima Report Functions (Existing, kept as is) ---

def load_posts() -> List[Dict[str, Any]]:
    if PRINCIPESSINA_PATH.exists():
        with open(PRINCIPESSINA_PATH, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_posts(posts: List[Dict[str, Any]]) -> None:
    with open(PRINCIPESSINA_PATH, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

def add_report(author: str, report_type: str, text_content: str) -> int:
    reports = load_posts()
    next_id = max((int(r.get("id", 0)) for r in reports), default=0) + 1
    new_report_entry = {
        "id": next_id, "author": author, "report_type": report_type,
        "text_content": text_content, "timestamp": datetime.now().isoformat(timespec="seconds"),
        "status": "active", "archived_timestamp": None,
    }
    reports.append(new_report_entry)
    save_posts(reports)
    return next_id

def delete_post(report_id: int) -> bool:
    reports = load_posts()
    original_length = len(reports)
    new_reports = [r for r in reports if r.get("id") != report_id]
    if len(new_reports) < original_length:
        save_posts(new_reports)
        return True
    return False

def filter_posts(author: str = "", keyword: str = "") -> List[Dict[str, Any]]:
    return []

def archive_report(report_id: int) -> bool:
    reports = load_posts()
    report_found = False
    for report in reports:
        if report.get("id") == report_id:
            if report.get("status") == "active":
                report["status"] = "archived"
                report["archived_timestamp"] = datetime.now().isoformat(timespec="seconds")
                report_found = True
            break
    if report_found:
        save_posts(reports)
        return True
    return False

def get_active_reports(report_type: Optional[str] = None) -> List[Dict[str, Any]]:
    reports = load_posts()
    active_reports = [r for r in reports if r.get("status") == "active"]
    if report_type:
        active_reports = [r for r in active_reports if r.get("report_type") == report_type]
    return active_reports

def get_archived_reports() -> List[Dict[str, Any]]:
    reports = load_posts()
    return [r for r in reports if r.get("status") == "archived"]

# --- Decima Media Functions (New and Updated) ---

def load_media_entries() -> List[Dict[str, Any]]:
    if MEDIA_PATH.exists():
        with open(MEDIA_PATH, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_media_entries(entries: List[Dict[str, Any]]) -> None:
    with open(MEDIA_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

def add_media_entry(
    uploader_username: str, media_type: str, original_filename: str, 
    server_filepath: str, title: Optional[str] = None, 
    custom_folder_name: Optional[str] = None
) -> int:
    entries = load_media_entries()
    next_id = max((int(e.get("id", 0)) for e in entries), default=0) + 1
    new_entry = {
        "id": next_id, "uploader_username": uploader_username, "media_type": media_type,
        "title": title, "original_filename": original_filename,
        "server_filepath": server_filepath, "custom_folder_name": custom_folder_name,
        "upload_timestamp": datetime.now().isoformat(timespec="seconds")
    }
    entries.append(new_entry)
    save_media_entries(entries)
    return next_id

def get_media_entries(
    media_type: Optional[str] = None, 
    custom_folder_name: Optional[str] = None # If None, get non-custom. If string, get specific custom.
) -> List[Dict[str, Any]]:
    entries = load_media_entries()
    if media_type:
        entries = [e for e in entries if e.get("media_type") == media_type]
    
    if custom_folder_name is None: # Requesting entries NOT in a custom folder
        entries = [e for e in entries if not e.get("custom_folder_name")]
    else: # Requesting entries IN a specific custom folder
        entries = [e for e in entries if e.get("custom_folder_name") == custom_folder_name]
        
    return entries

def delete_media_entry(media_id: int, base_static_uploads_path: str) -> bool:
    # base_static_uploads_path is 'static/uploads'
    entries = load_media_entries()
    original_length = len(entries)
    entry_to_delete = None
    for entry in entries:
        if entry.get("id") == media_id:
            entry_to_delete = entry
            break
    if not entry_to_delete: return False

    if entry_to_delete.get("server_filepath"):
        try:
            # server_filepath is like 'principessina/videos/2023/10/w42/filename.ext'
            # or 'principessina/videos/custom/my_folder/filename.ext'
            # It's relative to 'static/uploads/'
            full_file_path = os.path.join(base_static_uploads_path, entry_to_delete["server_filepath"])
            if os.path.exists(full_file_path):
                os.remove(full_file_path)
        except Exception: # Log error e.g. print(f"Error deleting file {full_file_path}: {e}")
            pass 
    
    new_entries = [e for e in entries if e.get("id") != media_id]
    if len(new_entries) < original_length:
        save_media_entries(new_entries)
        return True
    if not new_entries and original_length == 1 and entry_to_delete: # Deleted the only entry
        save_media_entries(new_entries)
        return True
    return False

def ensure_media_folder_structure(
    base_principessina_upload_path: str, # e.g., 'static/uploads/principessina'
    media_type: str, # 'videos' or 'photos'
    year: int, month: int, week: int
) -> str:
    # Returns path relative to base_principessina_upload_path, e.g., 'videos/2023/10/42'
    year_str, month_str, week_str = str(year), f"{month:02d}", f"{week:02d}"
    relative_path = os.path.join(media_type, year_str, month_str, f"w{week_str}")
    full_path = os.path.join(base_principessina_upload_path, relative_path)
    os.makedirs(full_path, exist_ok=True)
    return relative_path

def create_custom_media_folder(
    base_principessina_media_type_path: str, # e.g., 'static/uploads/principessina/videos'
    user_folder_name: str
) -> Tuple[bool, str]:
    # Validate folder_name
    if not user_folder_name or len(user_folder_name) > 100:
        return False, "フォルダ名は1文字以上100文字以内で入力してください。"
    if ".." in user_folder_name or "/" in user_folder_name or "\\" in user_folder_name:
        return False, "フォルダ名に無効な文字が含まれています ('..', '/', '\\')。"
    # Basic regex for typical "safe" folder names (alphanumeric, underscore, hyphen)
    if not re.match(r'^[a-zA-Z0-9_-]+$', user_folder_name):
        return False, "フォルダ名には英数字、アンダースコア(_)、ハイフン(-)のみ使用できます。"

    try:
        # Path for custom folder: base_principessina_media_type_path/custom/<user_folder_name>
        custom_folder_path = os.path.join(base_principessina_media_type_path, "custom", user_folder_name)
        if os.path.exists(custom_folder_path):
            return False, f"フォルダ「{user_folder_name}」は既に存在します。"
        
        os.makedirs(custom_folder_path, exist_ok=True)
        return True, f"フォルダ「{user_folder_name}」を作成しました。"
    except Exception as e:
        # Log error: print(f"Error creating custom folder {user_folder_name}: {e}")
        return False, f"フォルダ作成中にエラーが発生しました: {e}"

def get_custom_folders(
    base_principessina_media_type_path: str # e.g., 'static/uploads/principessina/videos'
) -> List[str]:
    """Lists custom folder names under base_principessina_media_type_path/custom/."""
    custom_base_dir = os.path.join(base_principessina_media_type_path, "custom")
    if not os.path.isdir(custom_base_dir):
        return []
    try:
        return [
            d for d in os.listdir(custom_base_dir) 
            if os.path.isdir(os.path.join(custom_base_dir, d))
        ]
    except OSError: # E.g., permission denied
        return []
