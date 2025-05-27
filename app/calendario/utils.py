"""Utility functions for Calendario."""

import json
from datetime import date, timedelta
from pathlib import Path
from typing import List, Dict, Set, Optional, Iterable, Any

import config # Assuming config is accessible
from app.utils import send_email # Assuming this is a general email utility from another module


def _notify_all(subject: str, body: str) -> None:
    """Send email notification to all configured users."""
    for user_info_val in config.USERS.values(): # Renamed to avoid conflict
        email = user_info_val.get("email")
        if email:
            send_email(subject, body, email)


def _notify_event(action: str, event_data: Dict[str, Any], old_date_val: str = "") -> None:
    """Notify all users about calendar event changes."""
    title = event_data.get("title", "")
    date_str = event_data.get("date", "") # Expected to be an ISO date string
    
    body = ""
    if action == "add":
        body = f"{date_str} に '{title}' が追加されました。"
    elif action == "delete":
        body = f"{date_str} の '{title}' が削除されました。"
    elif action == "move":
        body = f"'{title}' の日付が {old_date_val} から {date_str} に変更されました。"
    elif action == "assign":
        emp = event_data.get("employee", "")
        body = f"{date_str} の '{title}' の担当が {emp} に設定されました。"
    elif action == "update":
        body = f"{date_str} の '{title}' が更新されました。"
    else:
        body = f"イベント '{title}' ({date_str}) に関する通知: アクション '{action}'。"

    if body:
        _notify_all("カレンダー更新", body)

DEFAULT_RULES: Dict[str, Any] = {
    "max_consecutive_days": 5,
    "min_staff_per_day": 1,
    "forbidden_pairs": [],
    "required_pairs": [],
    "required_attributes": {},
    "employee_attributes": {},
    # "defined_attributes" will be added here by save_rules
}

DEFAULT_DEFINED_ATTRIBUTES = ["Dog", "Lady", "Man", "Kaji", "Massage"] # Default list

EVENTS_PATH = Path(getattr(config, "CALENDAR_FILE", "events.json"))
RULES_PATH = Path(getattr(config, "CALENDAR_RULES_FILE", "calendar_rules.json"))


def load_events() -> List[Dict[str, Any]]:
    if EVENTS_PATH.exists():
        with open(EVENTS_PATH, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return [] # Return empty list if JSON is invalid
    return []


def save_events(events_list: List[Dict[str, Any]]) -> None:
    with open(EVENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(events_list, f, ensure_ascii=False, indent=2)


def get_event_by_id(event_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single event by its ID."""
    events = load_events()
    for event_item in events:
        if event_item.get("id") == event_id:
            return event_item
    return None


def add_event(
    event_date_obj: date, # Renamed for clarity
    title: str,
    description: str,
    employee: str,
    category: str = "other",
    participants: Optional[Iterable[str]] = None,
) -> None:
    events = load_events()
    next_id = max((e.get("id", 0) for e in events), default=0) + 1
    new_event = {
        "id": next_id,
        "date": event_date_obj.isoformat(),
        "title": title,
        "description": description,
        "employee": employee,
        "category": category,
        "participants": list(participants or []),
    }
    events.append(new_event)
    save_events(events)
    _notify_event("add", new_event) # Pass the new_event dict
    check_rules_and_notify()

    if category == "lesson":
        from app.corso import utils as corso_utils # Keep local import
        corso_utils.add_post(
            "system", title, description or "lesson scheduled", None, None,
        )


def update_event(event_id: int, form_data: Dict[str, Any]) -> bool: # Renamed new_data to form_data
    """Update an existing event with new data from a form."""
    events = load_events()
    event_idx = -1
    for i, ev_item in enumerate(events):
        if ev_item.get("id") == event_id:
            event_idx = i
            break

    if event_idx != -1:
        current_event_id = events[event_idx]['id'] # Preserve original ID
        
        # Prepare data for update, ensuring date is ISO string
        update_payload = form_data.copy()
        if 'date' in update_payload and isinstance(update_payload['date'], date):
            update_payload['date'] = update_payload['date'].isoformat()

        events[event_idx].update(update_payload)
        events[event_idx]['id'] = current_event_id # Ensure ID is not changed
        
        updated_event_for_notification = events[event_idx].copy()

        save_events(events)
        _notify_event("update", updated_event_for_notification)
        check_rules_and_notify() 
        return True
    return False


def delete_event(event_id: int) -> bool:
    events = load_events()
    event_to_delete = None
    for ev_item in events: # Renamed e to ev_item
        if ev_item.get("id") == event_id:
            event_to_delete = ev_item.copy() # Copy for notification
            break
            
    new_events_list = [e for e in events if e.get("id") != event_id] # Renamed
    
    deleted = False
    if len(new_events_list) < len(events):
        deleted = True
        save_events(new_events_list)
        if event_to_delete: 
            _notify_event("delete", event_to_delete)
        check_rules_and_notify()
    return deleted


def load_rules() -> tuple[Dict[str, Any], List[str]]: # Return type changed
    rules_dict = DEFAULT_RULES.copy() # Start with defaults
    if RULES_PATH.exists():
        with open(RULES_PATH, "r", encoding="utf-8") as f:
            try:
                loaded_rules = json.load(f)
                rules_dict.update(loaded_rules) # Update defaults with loaded rules
            except json.JSONDecodeError:
                pass # Keep defaults if JSON is invalid
    
    # Load defined_attributes, defaulting if not present in the file or if file doesn't exist
    defined_attributes = rules_dict.get("defined_attributes", DEFAULT_DEFINED_ATTRIBUTES[:]) # Use a copy
    # Ensure what's in rules_dict["defined_attributes"] is actually used if it exists
    if "defined_attributes" in rules_dict and isinstance(rules_dict["defined_attributes"], list):
        defined_attributes = rules_dict["defined_attributes"]
    else: # If not in file or not a list, set it from default and it will be saved next time
        rules_dict["defined_attributes"] = DEFAULT_DEFINED_ATTRIBUTES[:]


    return rules_dict, defined_attributes


def save_rules(rules_data: Dict[str, Any], defined_attributes: List[str]) -> None:
    rules_to_save = rules_data.copy()
    rules_to_save["defined_attributes"] = defined_attributes
    with open(RULES_PATH, "w", encoding="utf-8") as f:
        json.dump(rules_to_save, f, ensure_ascii=False, indent=2)


def parse_pairs(text: str) -> List[List[str]]:
    pairs: List[List[str]] = []
    for item in text.split(','):
        names = [p.strip() for p in item.split('-') if p.strip()]
        if len(names) >= 2:
            pairs.append(names[:2])
    return pairs


def parse_kv(text: str) -> Dict[str, object]:
    result: Dict[str, object] = {}
    for item in text.split(','):
        if ':' not in item:
            continue
        key_str, val_str = item.split(':', 1) # Renamed
        key_str = key_str.strip()
        val_str = val_str.strip()
        if not key_str or not val_str:
            continue
        if '|' in val_str:
            result[key_str] = [p.strip() for p in val_str.split('|') if p.strip()]
        else:
            result[key_str] = val_str
    return result


def parse_kv_int(text: str) -> Dict[str, int]:
    result: Dict[str, int] = {}
    for item in text.split(','):
        if ':' not in item:
            continue
        key_str, val_str = item.split(':', 1) # Renamed
        key_str = key_str.strip()
        val_str = val_str.strip()
        if not key_str or not val_str:
            continue
        try:
            result[key_str] = int(val_str)
        except ValueError:
            pass # Skip if value is not a valid integer
    return result


def move_event(event_id: int, new_event_date: date) -> bool: # Renamed new_date
    events = load_events()
    updated = False
    changed_event_copy = None 
    original_date_str = ""    

    for ev_item in events: # Renamed e to ev_item
        if ev_item.get("id") == event_id:
            original_date_str = ev_item.get("date", "")
            ev_item["date"] = new_event_date.isoformat()
            updated = True
            changed_event_copy = ev_item.copy() 
            break
    if updated:
        save_events(events)
        if changed_event_copy:
            _notify_event("move", changed_event_copy, original_date_str)
        check_rules_and_notify()
    return updated


def assign_employee(event_id: int, employee_name: str) -> bool: # Renamed employee
    events = load_events()
    updated = False
    changed_event_copy = None

    for ev_item in events: # Renamed e to ev_item
        if ev_item.get("id") == event_id:
            ev_item["employee"] = employee_name
            updated = True
            changed_event_copy = ev_item.copy()
            break
    if updated:
        save_events(events)
        if changed_event_copy:
            _notify_event("assign", changed_event_copy)
        check_rules_and_notify()
    return updated


def set_shift_schedule(month_date: date, schedule_data: Dict[str, List[str]]) -> None: # Renamed
    events = load_events()
    # Remove existing shifts for the month
    events = [
        e for e in events
        if not (
            e.get("category") == "shift"
            and e.get("date", "").startswith(month_date.strftime("%Y-%m"))
        )
    ]
    next_id = max((e.get("id", 0) for e in events), default=0) + 1
    
    newly_added_shifts = [] 
    for day_iso_str, emps_list in schedule_data.items(): # Renamed
        for emp_name_val in emps_list: # Renamed
            new_shift = {
                "id": next_id,
                "date": day_iso_str,
                "title": emp_name_val, 
                "description": "",
                "employee": emp_name_val,
                "category": "shift",
                "participants": [],
            }
            events.append(new_shift)
            newly_added_shifts.append(new_shift.copy())
            next_id += 1
            
    save_events(events)
    for shift_ev in newly_added_shifts: 
        _notify_event("add", shift_ev)
    check_rules_and_notify()


def get_admin_email_address() -> Optional[str]: # Renamed
    for user_cfg in config.USERS.values(): # Renamed
        if user_cfg.get("role") == "admin" and user_cfg.get("email"):
            return user_cfg["email"]
    return getattr(config, "ADMIN_EMAIL", None) 


def check_rules_and_notify() -> None:
    rules = load_rules()
    events = load_events()
    admin_email_addr = get_admin_email_address() # Renamed

    # Max consecutive days check
    events_by_employee: Dict[str, List[date]] = {}
    for event_item_rule_check in events: # Renamed
        emp_name_rule = event_item_rule_check.get("employee") # Renamed
        event_date_iso_str = event_item_rule_check.get("date") # Renamed
        if not emp_name_rule or not event_date_iso_str:
            continue
        try:
            event_dt_obj = date.fromisoformat(event_date_iso_str) # Renamed
            events_by_employee.setdefault(emp_name_rule, []).append(event_dt_obj)
        except ValueError:
            print(f"Warning: Invalid date format '{event_date_iso_str}' for event ID {event_item_rule_check.get('id')} in rule check.")
            continue

    max_consecutive = rules.get("max_consecutive_days", 9999)
    if isinstance(max_consecutive, str): 
        try: max_consecutive = int(max_consecutive)
        except ValueError: max_consecutive = 9999

    for emp_name_rule, work_dates in events_by_employee.items(): # Renamed
        work_dates.sort()
        consecutive_count = 0 # Renamed
        if work_dates:
            consecutive_count = 1
            for i in range(1, len(work_dates)):
                if work_dates[i] == work_dates[i - 1] + timedelta(days=1):
                    consecutive_count += 1
                    if consecutive_count > max_consecutive:
                        if admin_email_addr:
                            msg = f"{emp_name_rule} が {consecutive_count} 日連続で勤務しています (上限: {max_consecutive}日)。日付: {work_dates[i-consecutive_count+1].isoformat()} から {work_dates[i].isoformat()}"
                            send_email("連勤警告", msg, admin_email_addr)
                        break 
                else:
                    consecutive_count = 1
    
    # Min staff per day check
    min_staff = rules.get("min_staff_per_day", 1)
    if isinstance(min_staff, str):
        try: min_staff = int(min_staff)
        except ValueError: min_staff = 1

    events_by_date_staff_count: Dict[str, int] = {} # Renamed
    for event_item_min_staff in events: # Renamed
        date_iso = event_item_min_staff.get("date") # Renamed
        if date_iso:
            events_by_date_staff_count[date_iso] = events_by_date_staff_count.get(date_iso, 0) + 1
    
    for date_iso, staff_num in events_by_date_staff_count.items(): # Renamed
        if staff_num < min_staff:
            if admin_email_addr:
                send_email("人数不足警告", f"{date_iso} の勤務者数は {staff_num} 人です (最低必要数: {min_staff}人)。", admin_email_addr)

    # Advanced rule checks (pairs, attributes)
    events_by_date_employee_list: Dict[str, List[str]] = {} # Renamed
    for event_item_adv_rules in events: # Renamed
        emp_name_adv = event_item_adv_rules.get("employee") # Renamed
        date_iso_adv = event_item_adv_rules.get("date") # Renamed
        if not emp_name_adv or not date_iso_adv:
            continue
        events_by_date_employee_list.setdefault(date_iso_adv, []).append(emp_name_adv)

    forbidden_pairs_list = rules.get("forbidden_pairs", []) # Renamed
    required_pairs_list = rules.get("required_pairs", []) # Renamed
    required_attributes_map = rules.get("required_attributes", {}) # Renamed
    employee_attributes_map = rules.get("employee_attributes", {}) # Renamed

    for date_iso_adv_check, emps_on_day_list in events_by_date_employee_list.items(): # Renamed
        for pair_forbidden in forbidden_pairs_list: # Renamed
            if len(pair_forbidden) >= 2 and pair_forbidden[0] in emps_on_day_list and pair_forbidden[1] in emps_on_day_list:
                if admin_email_addr:
                    send_email("組み合わせ禁止警告", f"{date_iso_adv_check} にて {pair_forbidden[0]} と {pair_forbidden[1]} が同時に勤務しています（禁止設定）。", admin_email_addr)
        
        for pair_required in required_pairs_list: # Renamed
            if len(pair_required) >= 2:
                emp_a, emp_b = pair_required[0], pair_required[1]
                if (emp_a in emps_on_day_list and emp_b not in emps_on_day_list) or \
                   (emp_b in emps_on_day_list and emp_a not in emps_on_day_list):
                    if admin_email_addr:
                        send_email("組み合わせ不足警告", f"{date_iso_adv_check} にて {emp_a} と {emp_b} はペア勤務が必要です（片方のみ勤務中）。", admin_email_addr)
        
        if required_attributes_map:
            current_day_attr_counts: Dict[str, int] = {k: 0 for k in required_attributes_map} # Renamed
            for emp_name_attr_check in emps_on_day_list: # Renamed
                emp_attr_value = employee_attributes_map.get(emp_name_attr_check) # Renamed
                if isinstance(emp_attr_value, list):
                    for single_attr_item in emp_attr_value: # Renamed
                        if single_attr_item in current_day_attr_counts:
                            current_day_attr_counts[single_attr_item] += 1
                elif emp_attr_value in current_day_attr_counts:
                    current_day_attr_counts[emp_attr_value] += 1
            
            for req_attr_name, min_attr_count in required_attributes_map.items(): # Renamed
                actual_min_count = min_attr_count
                if isinstance(actual_min_count, str): 
                    try: actual_min_count = int(actual_min_count)
                    except ValueError: continue 
                
                if current_day_attr_counts.get(req_attr_name, 0) < actual_min_count:
                    if admin_email_addr:
                        msg = f"{date_iso_adv_check} にて属性 '{req_attr_name}' の必要勤務者数 {actual_min_count}人を満たしていません（現在: {current_day_attr_counts.get(req_attr_name, 0)}人）。"
                        send_email("属性不足警告", msg, admin_email_addr)


def compute_employee_stats(
    start_date_param: Optional[date] = None, end_date_param: Optional[date] = None # Renamed
) -> Dict[str, Dict[str, int]]:
    events = load_events()
    stats_by_employee: Dict[str, Set[date]] = {} # Renamed
    for event_item_stats in events: # Renamed
        emp_name_stats = event_item_stats.get("employee") # Renamed
        date_iso_str_stats = event_item_stats.get("date") # Renamed
        if not emp_name_stats or not date_iso_str_stats:
            continue
        try:
            event_date_obj_stats = date.fromisoformat(date_iso_str_stats) # Renamed
        except ValueError:
            continue
        if start_date_param and event_date_obj_stats < start_date_param:
            continue
        if end_date_param and event_date_obj_stats > end_date_param:
            continue
        stats_by_employee.setdefault(emp_name_stats, set()).add(event_date_obj_stats)

    total_days_in_range_val = None # Renamed
    if start_date_param is not None and end_date_param is not None:
        if end_date_param < start_date_param: 
            total_days_in_range_val = 0
        else:
            total_days_in_range_val = (end_date_param - start_date_param).days + 1

    final_stats: Dict[str, Dict[str, int]] = {} # Renamed
    for emp_name_stats_final, worked_dates_set in stats_by_employee.items(): # Renamed
        num_work_days = len(worked_dates_set) # Renamed
        emp_data: Dict[str, int] = {"work_days": num_work_days} # Renamed
        if total_days_in_range_val is not None:
            emp_data["off_days"] = total_days_in_range_val - num_work_days
        final_stats[emp_name_stats_final] = emp_data
    return final_stats
