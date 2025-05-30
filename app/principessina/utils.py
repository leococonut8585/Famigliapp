"""Utility functions for Decima Reports and Media."""

from datetime import datetime, date # Ensure date is imported
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import os
import re

import config

# --- Settings for Decima Reports (Text-based) ---
PRINCIPESSINA_PATH = Path(
    getattr(config, "PRINCIPESSINA_FILE", "principessina.json")
)
REPORT_FOLDERS_PATH = Path(
    getattr(config, "PRINCIPESSINA_REPORT_FOLDERS_FILE", "principessina_report_folders.json")
)

# --- Settings for Decima Media (Video/Photo) ---
MEDIA_PATH = Path(
    getattr(config, "PRINCIPESSINA_MEDIA_FILE", "principessina_media.json")
)
ALLOWED_VIDEO_EXTS = {'mp4', 'mov', 'avi', 'wmv', 'mkv', 'webm'}
ALLOWED_PHOTO_EXTS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
MAX_MEDIA_SIZE = 3 * 1024 * 1024 * 1024 # 3GB

# --- Decima Report Functions ---

def load_posts() -> List[Dict[str, Any]]:
    if PRINCIPESSINA_PATH.exists():
        with open(PRINCIPESSINA_PATH, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except json.JSONDecodeError: return []
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
        "custom_folder_name": None,
        "referenced_in_custom_folders": []
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

def get_archived_reports(
    custom_folder_name: Optional[str] = None,
    search_phrase: Optional[str] = None,
    search_date_from: Optional[date] = None,
    search_date_to: Optional[date] = None
) -> List[Dict[str, Any]]:
    all_reports = load_posts()
    # First, filter for archived status
    candidate_reports = [r for r in all_reports if r.get("status") == "archived"]

    # Then, filter based on custom_folder_name logic
    if custom_folder_name:
        candidate_reports = [
            r for r in candidate_reports
            if r.get("custom_folder_name") == custom_folder_name or \
               custom_folder_name in r.get("referenced_in_custom_folders", [])
        ]
    else: # Viewing non-custom primary location reports
        candidate_reports = [
            r for r in candidate_reports if not r.get("custom_folder_name")
        ]

    # Phrase Search
    if search_phrase:
        candidate_reports = [
            r for r in candidate_reports
            if search_phrase.lower() in r.get('text_content', '').lower()
        ]

    # Date Range Search (on original 'timestamp')
    if search_date_from:
        candidate_reports = [
            r for r in candidate_reports
            if r.get('timestamp') and datetime.fromisoformat(r['timestamp']).date() >= search_date_from
        ]
    if search_date_to:
        candidate_reports = [
            r for r in candidate_reports
            if r.get('timestamp') and datetime.fromisoformat(r['timestamp']).date() <= search_date_to
        ]

    candidate_reports.sort(key=lambda r: r.get('archived_timestamp') or '', reverse=True)
    return candidate_reports

# --- Report Custom Folder Management ---
def load_report_folder_names() -> List[str]:
    if REPORT_FOLDERS_PATH.exists():
        with open(REPORT_FOLDERS_PATH, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return data.get("folder_names", [])
            except json.JSONDecodeError: return []
    return []

def save_report_folder_names(names: List[str]) -> None:
    with open(REPORT_FOLDERS_PATH, "w", encoding="utf-8") as f:
        json.dump({"folder_names": sorted(list(set(names)))}, f, ensure_ascii=False, indent=2)

def get_custom_folders_for_reports() -> List[str]:
    return load_report_folder_names()

def create_report_custom_folder(folder_name: str) -> Tuple[bool, str]:
    if not folder_name or len(folder_name) > 100:
        return False, "フォルダ名は1文字以上100文字以内で入力してください。"
    if ".." in folder_name or "/" in folder_name or "\\" in folder_name:
        return False, "フォルダ名に無効な文字が含まれています。"
    if not re.match(r'^[a-zA-Z0-9_ -]+$', folder_name):
        return False, "フォルダ名には英数字、スペース、アンダースコア(_)、ハイフン(-)のみ使用できます。"
    folder_names = load_report_folder_names()
    if folder_name in folder_names:
        return False, f"フォルダ「{folder_name}」は既に存在します。"
    folder_names.append(folder_name)
    save_report_folder_names(folder_names)
    return True, f"フォルダ「{folder_name}」を作成しました。"

def add_report_reference_to_custom_folder(report_id: int, target_folder_name: str) -> bool:
    reports = load_posts()
    report_found_and_updated = False
    for report in reports:
        if report.get("id") == report_id:
            if report.get("custom_folder_name") == target_folder_name: return False
            references = report.setdefault("referenced_in_custom_folders", [])
            if target_folder_name not in references:
                references.append(target_folder_name)
                report_found_and_updated = True
            else: return True
            break
    if report_found_and_updated:
        save_posts(reports)
        return True
    return False

def remove_report_reference_from_custom_folder(report_id: int, target_folder_name: str) -> bool:
    reports = load_posts()
    report_found = False; list_modified = False
    for report in reports:
        if report.get("id") == report_id:
            report_found = True
            references = report.get("referenced_in_custom_folders", [])
            if target_folder_name in references:
                references.remove(target_folder_name)
                list_modified = True
            break
    if not report_found: return False
    if list_modified: save_posts(reports)
    return True

# --- Decima Media Functions ---
# (These remain unchanged from previous steps)
def load_media_entries() -> List[Dict[str, Any]]:
    if MEDIA_PATH.exists():
        with open(MEDIA_PATH, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except json.JSONDecodeError: return []
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
        "upload_timestamp": datetime.now().isoformat(timespec="seconds"),
        "referenced_in_custom_folders": []
    }
    entries.append(new_entry)
    save_media_entries(entries)
    return next_id

def get_media_entries(
    media_type: Optional[str] = None,
    custom_folder_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    all_entries = load_media_entries()
    if media_type:
        candidate_entries = [e for e in all_entries if e.get("media_type") == media_type]
    else: candidate_entries = all_entries
    filtered_entries = []
    for entry in candidate_entries:
        entry_primary_custom_folder = entry.get("custom_folder_name")
        entry_referenced_folders = entry.get("referenced_in_custom_folders", [])
        if custom_folder_name:
            if entry_primary_custom_folder == custom_folder_name or \
               custom_folder_name in entry_referenced_folders:
                filtered_entries.append(entry)
        else:
            if not entry_primary_custom_folder:
                filtered_entries.append(entry)
    return filtered_entries

def delete_media_entry(media_id: int, base_static_uploads_path: str) -> bool:
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
            full_file_path = os.path.join(base_static_uploads_path, entry_to_delete["server_filepath"])
            if os.path.exists(full_file_path): os.remove(full_file_path)
        except Exception: pass
    new_entries = [e for e in entries if e.get("id") != media_id]
    if len(new_entries) < original_length:
        save_media_entries(new_entries)
        return True
    if not new_entries and original_length == 1 and entry_to_delete:
        save_media_entries(new_entries)
        return True
    return False

def ensure_media_folder_structure(
    base_principessina_upload_path: str, media_type: str,
    year: int, month: int, week: int
) -> str:
    year_str, month_str, week_str = str(year), f"{month:02d}", f"{week:02d}"
    relative_path = os.path.join(media_type, year_str, month_str, f"w{week_str}")
    full_path = os.path.join(base_principessina_upload_path, relative_path)
    os.makedirs(full_path, exist_ok=True)
    return relative_path

def create_custom_media_folder(
    base_principessina_media_type_path: str, user_folder_name: str
) -> Tuple[bool, str]:
    if not user_folder_name or len(user_folder_name) > 100:
        return False, "フォルダ名は1文字以上100文字以内で入力してください。"
    if ".." in user_folder_name or "/" in user_folder_name or "\\" in user_folder_name:
        return False, "フォルダ名に無効な文字が含まれています ('..', '/', '\\')。"
    if not re.match(r'^[a-zA-Z0-9_-]+$', user_folder_name):
        return False, "フォルダ名には英数字、アンダースコア(_)、ハイフン(-)のみ使用できます。"
    try:
        custom_folder_path = os.path.join(base_principessina_media_type_path, "custom", user_folder_name)
        if os.path.exists(custom_folder_path):
            return False, f"フォルダ「{user_folder_name}」は既に存在します。"
        os.makedirs(custom_folder_path, exist_ok=True)
        return True, f"フォルダ「{user_folder_name}」を作成しました。"
    except Exception as e:
        return False, f"フォルダ作成中にエラーが発生しました: {e}"

def get_custom_folders(base_principessina_media_type_path: str) -> List[str]:
    custom_base_dir = os.path.join(base_principessina_media_type_path, "custom")
    if not os.path.isdir(custom_base_dir): return []
    try:
        return [d for d in os.listdir(custom_base_dir) if os.path.isdir(os.path.join(custom_base_dir, d))]
    except OSError: return []

def add_media_reference_to_custom_folder(media_id: int, target_custom_folder_name: str) -> bool:
    entries = load_media_entries()
    entry_found_and_updated = False
    for entry in entries:
        if entry.get("id") == media_id:
            if entry.get("custom_folder_name") == target_custom_folder_name: return False
            references = entry.setdefault("referenced_in_custom_folders", [])
            if target_custom_folder_name not in references:
                references.append(target_custom_folder_name)
                entry_found_and_updated = True
            else: return True
            break
    if entry_found_and_updated:
        save_media_entries(entries)
        return True
    return False

def remove_media_reference_from_custom_folder(media_id: int, target_custom_folder_name: str) -> bool:
    entries = load_media_entries()
    entry_found = False; list_modified = False
    for entry in entries:
        if entry.get("id") == media_id:
            entry_found = True
            references = entry.get("referenced_in_custom_folders", [])
            if target_custom_folder_name in references:
                references.remove(target_custom_folder_name)
                list_modified = True
            break
    if not entry_found: return False
    if list_modified: save_media_entries(entries)
    return True
