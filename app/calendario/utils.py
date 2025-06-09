"""Utility functions for Calendario."""

import json
from datetime import date, timedelta, datetime, time
from pathlib import Path
from typing import List, Dict, Set, Optional, Iterable, Any
from collections import defaultdict
import calendar # Added calendar import

import config
from app.utils import send_email


def _notify_all(subject: str, body: str) -> None:
    for user_info_val in config.USERS.values():
        email = user_info_val.get("email")
        if email: send_email(subject, body, email)

def _notify_event(action: str, event_data: Dict[str, Any], old_date_val: str = "") -> None:
    print(f"LOG: {datetime.now()} - Entered _notify_event. Action: {action}, Event Title: {event_data.get('title')}")
    title = event_data.get("title", ""); date_str = event_data.get("date", "")
    body = ""
    if action == "add": body = f"{date_str} に '{title}' が追加されました。"
    elif action == "delete": body = f"{date_str} の '{title}' が削除されました。"
    elif action == "move": body = f"'{title}' の日付が {old_date_val} から {date_str} に変更されました。"
    elif action == "assign": body = f"{date_str} の '{title}' の担当が {event_data.get('employee', '')} に設定されました。"
    elif action == "update": body = f"{date_str} の '{title}' が更新されました。"
    else: body = f"イベント '{title}' ({date_str}) に関する通知: アクション '{action}'。"

    if body:
        print(f"LOG: {datetime.now()} - _notify_event: Checking if mail is enabled before calling _notify_all for action: {action}")
        if getattr(config, 'MAIL_ENABLED', True):
            print(f"LOG: {datetime.now()} - _notify_event: Mail is enabled. Calling _notify_all for action: {action}")
            _notify_all("カレンダー更新", body)
            print(f"LOG: {datetime.now()} - _notify_event: Returned from _notify_all for action: {action}")
        else:
            print(f"LOG: {datetime.now()} - _notify_event: Mail is disabled by config.MAIL_ENABLED. Skipped _notify_all for action: {action}")
    else:
        print(f"LOG: {datetime.now()} - _notify_event: No body generated for notification. Action: {action}")
    print(f"LOG: {datetime.now()} - Exiting _notify_event. Action: {action}")

DEFAULT_RULES: Dict[str, Any] = {
    "max_consecutive_days": 5, "min_staff_per_day": 1,
    "forbidden_pairs": [], "required_pairs": [],
    "required_attributes": {}, "employee_attributes": {},
    "specialized_requirements": {} # 追加
}
DEFAULT_DEFINED_ATTRIBUTES = ["Dog", "Lady", "Man", "Kaji", "Massage"]

EVENTS_PATH = Path(getattr(config, "CALENDAR_FILE", "events.json"))
RULES_PATH = Path(getattr(config, "CALENDAR_RULES_FILE", "calendar_rules.json"))

def load_events() -> List[Dict[str, Any]]:
    print(f"LOG: {datetime.now()} - Entered load_events")
    if EVENTS_PATH.exists():
        with open(EVENTS_PATH, "r", encoding="utf-8") as f:
            try:
                events = json.load(f)
                print(f"LOG: {datetime.now()} - Exiting load_events, loaded {len(events)} events")
                return events
            except json.JSONDecodeError:
                print(f"LOG: {datetime.now()} - Exiting load_events, JSONDecodeError")
                return []
    print(f"LOG: {datetime.now()} - Exiting load_events, file not found")
    return []

def save_events(events_list: List[Dict[str, Any]]) -> None:
    print(f"LOG: {datetime.now()} - Entered save_events, saving {len(events_list)} events")
    with open(EVENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(events_list, f, ensure_ascii=False, indent=2)
    print(f"LOG: {datetime.now()} - Exiting save_events")

def get_event_by_id(event_id: int) -> Optional[Dict[str, Any]]:
    print(f"LOG: {datetime.now()} - Entered get_event_by_id for event_id: {event_id}")
    events = load_events()
    for event_item in events:
        if event_item.get("id") == event_id:
            print(f"LOG: {datetime.now()} - Exiting get_event_by_id, event found.")
            return event_item
    print(f"LOG: {datetime.now()} - Exiting get_event_by_id, event not found.")
    return None

def add_event(
    event_date_obj: date, title: str, description: str, employee: str,
    category: str = "other", participants: Optional[Iterable[str]] = None,
    time: Optional[datetime.time] = None,
) -> None:
    events = load_events()
    next_id = max((e.get("id", 0) for e in events), default=0) + 1
    new_event = {
        "id": next_id, "date": event_date_obj.isoformat(), "title": title,
        "description": description, "employee": employee, "category": category,
        "participants": list(participants or []),
        "time": time.isoformat(timespec='minutes') if time else None,
    }
    events.append(new_event); save_events(events); _notify_event("add", new_event)
    check_rules_and_notify()
    if category == "lesson":
        from app.corso import utils as corso_utils
        corso_utils.add_post("system", title, description or "lesson scheduled", None, None)

def update_event(event_id: int, form_data: Dict[str, Any]) -> bool:
    events = load_events(); event_idx = -1
    for i, ev_item in enumerate(events):
        if ev_item.get("id") == event_id: event_idx = i; break
    if event_idx != -1:
        current_event_id = events[event_idx]['id']; update_payload = form_data.copy()
        if 'date' in update_payload and isinstance(update_payload['date'], date):
            update_payload['date'] = update_payload['date'].isoformat()
        if 'time' in update_payload and isinstance(update_payload['time'], time):
            update_payload['time'] = update_payload['time'].isoformat(timespec='minutes')
        elif 'time' in update_payload and update_payload['time'] is None: # Ensure None is stored if time is explicitly cleared
            update_payload['time'] = None
        events[event_idx].update(update_payload); events[event_idx]['id'] = current_event_id
        updated_event_for_notification = events[event_idx].copy()
        save_events(events); _notify_event("update", updated_event_for_notification)
        check_rules_and_notify(); return True
    return False

def delete_event(event_id: int) -> bool:
    events = load_events(); event_to_delete = None
    for ev_item in events:
        if ev_item.get("id") == event_id: event_to_delete = ev_item.copy(); break
    new_events_list = [e for e in events if e.get("id") != event_id]; deleted = False
    if len(new_events_list) < len(events):
        deleted = True; save_events(new_events_list)
        if event_to_delete: _notify_event("delete", event_to_delete)
        check_rules_and_notify()
    return deleted

def load_rules() -> tuple[Dict[str, Any], List[str]]:
    rules_dict = DEFAULT_RULES.copy() # specialized_requirements もコピーされる
    if RULES_PATH.exists():
        with open(RULES_PATH, "r", encoding="utf-8") as f:
            try:
                loaded_from_file = json.load(f)
                # 既存のキーのみを上書きし、新しいキー(specialized_requirementsなど)はデフォルトを維持
                for key in DEFAULT_RULES.keys(): # Iterate over keys in DEFAULT_RULES to ensure all are present
                    if key in loaded_from_file:
                        rules_dict[key] = loaded_from_file[key]
                    # If a key from DEFAULT_RULES is not in loaded_from_file, it keeps its default value from rules_dict = DEFAULT_RULES.copy()
                # Handle defined_attributes separately if it's stored outside DEFAULT_RULES structure in JSON but managed by it
                if "defined_attributes" in loaded_from_file:
                     rules_dict["defined_attributes"] = loaded_from_file["defined_attributes"]

            except json.JSONDecodeError:
                pass # デフォルトルールを使用

    defined_attributes = rules_dict.get("defined_attributes", DEFAULT_DEFINED_ATTRIBUTES[:])
    if not (isinstance(defined_attributes, list) and all(isinstance(attr, str) for attr in defined_attributes)):
        defined_attributes = DEFAULT_DEFINED_ATTRIBUTES[:]
    # Ensure defined_attributes is part of the main rules_dict for consistency if other parts of the app expect it there,
    # but it's returned separately as per function signature.
    # rules_dict["defined_attributes"] = defined_attributes # This line is a bit redundant if defined_attributes are loaded correctly into rules_dict

    # specialized_requirements がファイルにない場合や、読み込み時にキーが欠落した場合にデフォルトを保証
    # Also ensure it's a dictionary
    if "specialized_requirements" not in rules_dict or not isinstance(rules_dict.get("specialized_requirements"), dict):
        rules_dict["specialized_requirements"] = DEFAULT_RULES["specialized_requirements"].copy()

    # Remove defined_attributes from the returned rules_dict as it's returned separately
    # However, if other parts of the code expect it IN rules_dict, this might need adjustment.
    # For now, assuming routes.py and other consumers use the returned 'defined_attributes' list directly.
    # The `rules_for_js` in routes.py gets `rules.copy()`, so `defined_attributes` will be in there if present in `rules_dict`.
    # Let's keep `defined_attributes` within `rules_dict` for `rules_for_js` and general access,
    # while still returning it separately as per the function signature for direct use.
    # So, no need to `del rules_dict["defined_attributes"]`.

    return rules_dict, defined_attributes

def save_rules(
    rules_data: Dict[str, Any],
    defined_attributes: List[str],
    specialized_requirements_data: Dict[str, List[str]] # 新しい引数
) -> None:
    rules_to_save = rules_data.copy()
    # Ensure 'defined_attributes' from the argument list is authoritative
    rules_to_save["defined_attributes"] = defined_attributes
    rules_to_save["specialized_requirements"] = specialized_requirements_data # 専門予定データを追加
    with open(RULES_PATH, "w", encoding="utf-8") as f:
        json.dump(rules_to_save, f, ensure_ascii=False, indent=2)

def parse_pairs(text: str) -> List[List[str]]:
    pairs: List[List[str]] = [];_ = [pairs.append(names[:2]) for item in text.split(',') if item for names in [[p.strip() for p in item.split('-') if p.strip()]] if len(names) >= 2] if text else []
    return pairs

def parse_kv(text: str) -> Dict[str, object]:
    result: Dict[str, object] = {};_ = [ (result.update({key_str: [p.strip() for p in val_str.split('|') if p.strip()] if '|' in val_str else val_str})) for item in text.split(',') if item and ':' in item for key_str, val_str in [(item.split(':', 1)[0].strip(), item.split(':', 1)[1].strip())] if key_str] if text else []
    return result

def parse_kv_int(text: str) -> Dict[str, int]:
    result: Dict[str, int] = {}; _ = [ (result.update({key_str: int(val_str)})) for item in text.split(',') if item and ':' in item for key_str, val_str in [(item.split(':', 1)[0].strip(), item.split(':', 1)[1].strip())] if key_str and val_str.isdigit()] if text else [] # Simplified isdigit check, consider try-except int() for robustness
    return result

def move_event(event_id: int, new_event_date: date) -> bool:
    print(f"LOG: {datetime.now()} - Entered move_event for event_id: {event_id} to new_date: {new_event_date.isoformat()}")
    events = load_events(); updated = False; changed_event_copy = None; original_date_str = ""
    for ev_item in events:
        if ev_item.get("id") == event_id:
            original_date_str = ev_item.get("date", ""); ev_item["date"] = new_event_date.isoformat(); updated = True
            changed_event_copy = ev_item.copy(); break

    if updated:
        print(f"LOG: {datetime.now()} - Event {event_id} date updated in memory. Calling save_events.")
        save_events(events)
        print(f"LOG: {datetime.now()} - Returned from save_events for move. Calling _notify_event.")
        if changed_event_copy:
            _notify_event("move", changed_event_copy, original_date_str)
        print(f"LOG: {datetime.now()} - Returned from _notify_event for move. Calling check_rules_and_notify.")
        check_rules_and_notify()
        print(f"LOG: {datetime.now()} - Returned from check_rules_and_notify for move.")
    else:
        print(f"LOG: {datetime.now()} - Event {event_id} not found for moving.")

    print(f"LOG: {datetime.now()} - Exiting move_event. Updated: {updated}")
    return updated

def assign_employee(event_id: int, employee_name: str) -> bool:
    events = load_events(); updated = False; changed_event_copy = None
    for ev_item in events:
        if ev_item.get("id") == event_id:
            ev_item["employee"] = employee_name; updated = True; changed_event_copy = ev_item.copy(); break
    if updated: save_events(events); _notify_event("assign", changed_event_copy) if changed_event_copy else None; check_rules_and_notify()
    return updated

def set_shift_schedule(month_date: date, schedule_data: Dict[str, List[str]]) -> None:
    events = load_events(); events = [e for e in events if not (e.get("category") == "shift" and e.get("date", "").startswith(month_date.strftime("%Y-%m")))]
    next_id = max((e.get("id", 0) for e in events), default=0) + 1
    for day_iso_str, emps_list in schedule_data.items():
        for emp_name_val in emps_list:
            new_shift = {"id": next_id, "date": day_iso_str, "title": emp_name_val, "description": "", "employee": emp_name_val, "category": "shift", "participants": []}
            events.append(new_shift); next_id += 1
    save_events(events); check_rules_and_notify(send_notifications=False)

def get_admin_email_address() -> Optional[str]:
    for user_cfg in config.USERS.values():
        if user_cfg.get("role") == "admin" and user_cfg.get("email"): return user_cfg["email"]
    return getattr(config, "ADMIN_EMAIL", None) 

def check_rules_and_notify(send_notifications: bool = False) -> None:
    print(f"LOG: {datetime.now()} - Entered check_rules_and_notify. send_notifications: {send_notifications}")
    if not getattr(config, 'MAIL_ENABLED', True) and send_notifications:
        print(f"LOG: {datetime.now()} - Mail notifications are disabled by config.MAIL_ENABLED. Skipping actual notifications in check_rules_and_notify.")
        # If there were specific notification calls here, they would be skipped.
        # Since it's just 'pass' for now, this log indicates intent.

    # Current implementation is pass, so nothing complex to log inside.
    # If logic for rule checking that *leads* to notifications is added,
    # that logic might still run, but the notification *sending* part would be skipped.
    print(f"LOG: {datetime.now()} - Exiting check_rules_and_notify")
    pass

def get_users_on_shift(target_date: date) -> List[str]:
    events = load_events(); users_on_shift_today: Set[str] = set(); target_date_iso = target_date.isoformat()
    for event in events:
        if event.get('date') == target_date_iso and event.get('category') == 'shift' and event.get('employee'):
            users_on_shift_today.add(event['employee'])
    return list(users_on_shift_today)

def compute_employee_stats(start_date_param: Optional[date] = None, end_date_param: Optional[date] = None) -> Dict[str, Dict[str, int]]:
    events = load_events(); stats_by_employee: Dict[str, Set[date]] = defaultdict(set) # Use defaultdict
    for event_item_stats in events:
        emp_name_stats = event_item_stats.get("employee"); date_iso_str_stats = event_item_stats.get("date")
        if not emp_name_stats or not date_iso_str_stats: continue
        try: event_date_obj_stats = date.fromisoformat(date_iso_str_stats)
        except ValueError: continue
        if (start_date_param and event_date_obj_stats < start_date_param) or \
           (end_date_param and event_date_obj_stats > end_date_param): continue
        stats_by_employee[emp_name_stats].add(event_date_obj_stats)
    total_days_in_range_val = None
    if start_date_param and end_date_param and end_date_param >= start_date_param:
        total_days_in_range_val = (end_date_param - start_date_param).days + 1
    final_stats: Dict[str, Dict[str, int]] = {}
    for emp_name_stats_final, worked_dates_set in stats_by_employee.items():
        num_work_days = len(worked_dates_set)
        emp_data: Dict[str, int] = {"work_days": num_work_days}
        if total_days_in_range_val is not None: emp_data["off_days"] = total_days_in_range_val - num_work_days
        final_stats[emp_name_stats_final] = emp_data
    return final_stats

def get_shift_violations(assignments: Dict[str, List[str]], rules: Dict[str, Any], users_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    detected_violations: List[Dict[str, Any]] = []; defined_attributes = rules.get("defined_attributes", DEFAULT_DEFINED_ATTRIBUTES[:])
    if not (isinstance(defined_attributes, list) and all(isinstance(attr, str) for attr in defined_attributes)):
        defined_attributes = DEFAULT_DEFINED_ATTRIBUTES[:]
    max_consecutive = int(rules.get("max_consecutive_days", 9999)); employee_work_dates: Dict[str, List[date]] = defaultdict(list)
    sorted_assignment_dates = sorted(assignments.keys())
    for date_iso_str in sorted_assignment_dates:
        try:
            current_date_obj = date.fromisoformat(date_iso_str)
            for emp_name in assignments[date_iso_str]: employee_work_dates[emp_name].append(current_date_obj)
        except ValueError: print(f"Warning: Invalid date format '{date_iso_str}' in assignments for rule check."); continue
    for emp_name, work_dates in employee_work_dates.items():
        if not work_dates: continue; work_dates.sort(); consecutive_run = 0
        if work_dates:
            consecutive_run = 1
            for i in range(1, len(work_dates)):
                if work_dates[i] == work_dates[i-1] + timedelta(days=1): consecutive_run += 1
                else:
                    if consecutive_run > max_consecutive:
                        last_day_of_run = work_dates[i-1]
                        detected_violations.append({"date": last_day_of_run.isoformat(), "rule_type": "max_consecutive_days", "employee": emp_name, "description": f"{emp_name}さんは{consecutive_run}連勤です (最大{max_consecutive}日)。超過最終日: {last_day_of_run.isoformat()}", "details": {"current_consecutive": consecutive_run, "max_allowed": max_consecutive, "employee": emp_name, "offending_end_date": last_day_of_run.isoformat()}})
                    consecutive_run = 1
            if consecutive_run > max_consecutive:
                last_day_of_run = work_dates[-1]
                detected_violations.append({"date": last_day_of_run.isoformat(), "rule_type": "max_consecutive_days", "employee": emp_name, "description": f"{emp_name}さんは{consecutive_run}連勤です (最大{max_consecutive}日)。超過最終日: {last_day_of_run.isoformat()}", "details": {"current_consecutive": consecutive_run, "max_allowed": max_consecutive, "employee": emp_name, "offending_end_date": last_day_of_run.isoformat()}})
    min_staff = int(rules.get("min_staff_per_day", 0))
    for target_date_iso_str, assigned_emps in assignments.items():
        current_staff_count = len(assigned_emps)
        if current_staff_count < min_staff: detected_violations.append({"date": target_date_iso_str, "rule_type": "min_staff_per_day", "description": f"{target_date_iso_str}は最低{min_staff}人必要ですが、現在{current_staff_count}人です", "details": {"current_staff": current_staff_count, "min_required": min_staff, "date": target_date_iso_str}})
    forbidden_pairs_list = rules.get("forbidden_pairs", [])
    for target_date_iso_str, assigned_emps in assignments.items():
        assigned_emps_set = set(assigned_emps)
        for pair in forbidden_pairs_list:
            if len(pair) >= 2 and pair[0] in assigned_emps_set and pair[1] in assigned_emps_set: detected_violations.append({"date": target_date_iso_str, "rule_type": "forbidden_pair", "employees": pair, "description": f"{pair[0]}さんと{pair[1]}さんは{target_date_iso_str}に同時勤務が禁止されています", "details": {"pair": pair, "date": target_date_iso_str}})
    required_pairs_list = rules.get("required_pairs", [])
    for target_date_iso_str, assigned_emps in assignments.items():
        assigned_emps_set = set(assigned_emps)
        for pair in required_pairs_list:
            if len(pair) >= 2:
                empA, empB = pair[0], pair[1]; empA_present = empA in assigned_emps_set; empB_present = empB in assigned_emps_set
                if empA_present != empB_present:
                    missing_member = empB if empA_present else empA; present_member = empA if empA_present else empB
                    detected_violations.append({"date": target_date_iso_str, "rule_type": "required_pair", "employees": pair, "description": f"{pair[0]}さんと{pair[1]}さんは{target_date_iso_str}にペアでの勤務が必要です ({missing_member}さんがいません)", "details": {"pair": pair, "present_member": present_member, "missing_member": missing_member, "date": target_date_iso_str}})
    employee_attributes_map = rules.get("employee_attributes", {}); required_attributes_map = rules.get("required_attributes", {})
    for target_date_iso_str, assigned_emps in assignments.items():
        daily_attribute_counts: Dict[str, int] = defaultdict(int)
        for emp_name in assigned_emps:
            emp_attrs_raw = employee_attributes_map.get(emp_name, []); emp_attrs_list = [emp_attrs_raw] if isinstance(emp_attrs_raw, str) else emp_attrs_raw
            for attr in emp_attrs_list:
                if attr in defined_attributes: daily_attribute_counts[attr] += 1
        for req_attr_name, req_count_any in required_attributes_map.items():
            req_count = int(req_count_any); current_attr_count = daily_attribute_counts.get(req_attr_name, 0)
            if current_attr_count < req_count: detected_violations.append({"date": target_date_iso_str, "rule_type": "required_attribute_count", "attribute": req_attr_name, "description": f"{target_date_iso_str}には属性'{req_attr_name}'が最低{req_count}人必要ですが、現在{current_attr_count}人です", "details": {"current_count": current_attr_count, "required_count": req_count, "attribute": req_attr_name, "date": target_date_iso_str}})

    # 専門予定のチェック
    # Ensure 'specialized_requirements' key exists and is a dict, even if it's empty
    specialized_requirements = rules.get("specialized_requirements", {})
    if not isinstance(specialized_requirements, dict): # Should not happen if load_rules is correct
        specialized_requirements = {}

    if specialized_requirements:
        all_events = load_events() # 全イベントをロード
        events_by_date: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for event in all_events:
            event_date_str = event.get("date")
            if event_date_str: # Ensure date exists
                events_by_date[event_date_str].append(event)

        for target_date_iso_str, assigned_emps_on_day in assignments.items():
            # その日のイベントを取得
            day_events = events_by_date.get(target_date_iso_str, [])

            for event_category_key, required_staff_list in specialized_requirements.items():
                # event_category_key は "mummy", "tattoo" など
                # required_staff_list は ["sara", "hitomi"] など

                if not required_staff_list: # Skip if no staff are required for this category
                    continue

                # その日に専門予定カテゴリのイベントがあるかチェック
                category_event_exists_on_day = any(
                    ev.get("category") == event_category_key for ev in day_events
                )

                if category_event_exists_on_day:
                    # 必須担当者が割り当てられているかチェック
                    is_required_staff_assigned = any(
                        emp in assigned_emps_on_day for emp in required_staff_list
                    )

                    if not is_required_staff_assigned:
                        # 警告メッセージの担当者リスト部分を作成
                        required_staff_str = "または".join(required_staff_list)
                        # カテゴリ表示名 (実際のアプリケーションでは、キーから表示名へのマッピングが望ましい)
                        # 例: category_display_names = {"mummy": "マミー系", "tattoo": "タトゥー"}
                        # category_display_name = category_display_names.get(event_category_key, event_category_key)
                        category_display_name = event_category_key # For now, use key

                        description = f"{category_display_name}の予定がある日({target_date_iso_str})に{required_staff_str}が割り当てられていません"
                        detected_violations.append({
                            "date": target_date_iso_str,
                            "rule_type": "specialized_requirement_missing",
                            "category": event_category_key,
                            "description": description,
                            "details": {
                                "required_staff": required_staff_list,
                                "assigned_staff": assigned_emps_on_day,
                                "category": event_category_key,
                                "date": target_date_iso_str
                            }
                        })
    return detected_violations

# --- New function for Step 1 of this subtask ---
def calculate_consecutive_work_days_for_all(
    assignments: Dict[str, List[str]],
    target_month_start: date
) -> Dict[str, Dict[str, int]]:
    all_consecutive_info: Dict[str, Dict[str, int]] = defaultdict(dict)
    
    year = target_month_start.year
    month = target_month_start.month
    _, days_in_month = calendar.monthrange(year, month)
    target_month_end = date(year, month, days_in_month)

    all_employees_in_assignments: Set[str] = set()
    for emp_list in assignments.values():
        for emp_name in emp_list:
            all_employees_in_assignments.add(emp_name)

    for employee in all_employees_in_assignments:
        employee_work_dates: List[date] = []
        # Collect all dates this employee worked, across all provided assignments
        # This needs to include dates *before* the target_month_start to correctly calculate
        # consecutive days that roll into the target_month.
        # The 'assignments' dict should ideally contain data for at least one month prior if possible.
        for date_iso_str, emps_on_day in assignments.items():
            if employee in emps_on_day:
                try:
                    employee_work_dates.append(date.fromisoformat(date_iso_str))
                except ValueError:
                    # Log or handle malformed date string in assignments
                    print(f"Warning: Malformed date string '{date_iso_str}' in assignments for employee {employee}.")
                    continue
        
        if not employee_work_dates:
            continue

        employee_work_dates.sort() # Crucial for consecutive day calculation

        consecutive_days_count = 0
        for i, current_work_date in enumerate(employee_work_dates):
            if i == 0 or current_work_date != (employee_work_dates[i-1] + timedelta(days=1)):
                consecutive_days_count = 1 # Reset or start count
            else:
                consecutive_days_count += 1 # Increment consecutive days
            
            # Store the count if the date falls within the target month
            if target_month_start <= current_work_date <= target_month_end:
                all_consecutive_info[employee][current_work_date.isoformat()] = consecutive_days_count
                
    return dict(all_consecutive_info) # Convert defaultdict to dict for return if preferred

def another_initials_filter_for_japanese_names(name):
    if not name:
        return ""
    # For Japanese names like '山田太郎', just take the first character.
    # For romaji names like 'raito', it will also take the first char 'R'.
    return name[0].upper()
