"""Routes for Calendario."""

from datetime import datetime, date, timedelta
import calendar

import json
from flask import (
    render_template,
    session,
    redirect,
    url_for,
    flash,
    request,
    jsonify,
)

from . import bp
from .forms import EventForm, StatsForm, ShiftRulesForm, ShiftManagementForm
from . import utils
import config
from typing import Dict, List
import re
from collections import defaultdict

# Regex for parsing time from event titles
time_title_pattern = re.compile(r'^(\d{1,2}:\d{2})\s*(.*)$')

EVENT_SORT_PRIORITY = {
    "shucchou": 1,
    "hug": 2,
    "other_no_time": 3,
    "shift": 4,
    "other_with_time": 5,
    "mummy": 5, # 追加
    "tattoo": 5, # 追加
}

@bp.before_request
def require_login():
    if "user" not in session:
        return redirect(url_for("auth.login", next=request.url))


@bp.route("/")
def index():
    """Show calendar in month or week view."""
    user = session.get("user")
    view = request.args.get("view", "month")
    today = date.today() 
    month_param = request.args.get("month")
    week_param = request.args.get("week")
    limit_past_date = today.replace(year=today.year - 2)
    limit_future_date = today.replace(year=today.year + 2)
    try:
        if month_param: year, mon = map(int, month_param.split("-")); month = date(year, mon, 1)
        else: month = date(today.year, today.month, 1)
    except Exception: month = date(today.year, today.month, 1)
    if week_param:
        try: week_start = datetime.fromisoformat(week_param).date()
        except Exception: week_start = today - timedelta(days=today.weekday())
    else: week_start = today - timedelta(days=today.weekday())
    week_start = week_start - timedelta(days=week_start.weekday()) # Ensure week_start is a Monday

    events = utils.load_events()

    # 1. Add display_time and cleaned_title
    for event in events:
        title_match = time_title_pattern.match(event.get('title', ''))
        if title_match:
            event['display_time'] = title_match.group(1)
            event['cleaned_title'] = title_match.group(2).strip()
        else:
            event['display_time'] = None
            event['cleaned_title'] = event.get('title', '')

    # 2. Add sort_priority and sort_time
    for event in events:
        category = event.get('category', 'other')
        has_time = event.get('display_time') is not None

        if category == 'shucchou':
            event['sort_priority'] = EVENT_SORT_PRIORITY['shucchou']
            event['sort_time'] = "00:00"
        elif category == 'hug':
            event['sort_priority'] = EVENT_SORT_PRIORITY['hug']
            event['sort_time'] = "00:00" # Changed from "00:01" to match revised plan
        elif category == 'shift':
            event['sort_priority'] = EVENT_SORT_PRIORITY['shift']
            event['sort_time'] = "00:00"
        elif category in ['lesson', 'kouza', 'other', 'mummy', 'tattoo']:
            if has_time:
                event['sort_priority'] = EVENT_SORT_PRIORITY['other_with_time']
                event['sort_time'] = event['display_time']
            else: # Time not specified
                event['sort_priority'] = EVENT_SORT_PRIORITY['other_no_time']
                event['sort_time'] = "00:00" # Changed from "00:02"
        else: # Fallback
            event['sort_priority'] = 99
            event['sort_time'] = "23:59"

    # 3. Sort all events by date, then by new sort keys
    events.sort(key=lambda e: (e.get("date", ""), e.get('sort_priority', 99), e.get('sort_time', '23:59')))

    stats = {}
    if events:
        try: start_date_for_stats = date.fromisoformat(events[0].get("date"))
        except Exception: start_date_for_stats = None
        stats = utils.compute_employee_stats(start_date_param=start_date_for_stats, end_date_param=date.today())

    if view == "week":
        start_d = week_start; end_d = week_start + timedelta(days=6)
        week_days = [start_d + timedelta(days=i) for i in range(7)]; time_slots = []
        for hour in range(24): time_slots.append(f"{hour:02d}:00"); time_slots.append(f"{hour:02d}:30")

        # Filter from the globally sorted and augmented 'events' list
        raw_week_events = []
        for e_raw in events:
            try:
                event_date_obj = date.fromisoformat(e_raw.get("date"))
                if start_d <= event_date_obj <= end_d:
                    raw_week_events.append(e_raw)
            except (ValueError, TypeError): continue

        structured_events = defaultdict(lambda: defaultdict(list))
        for event_struct in raw_week_events:
            event_date_iso = event_struct.get("date")
            if event_struct.get('display_time'):
                time_parts = event_struct['display_time'].split(':')
                hour_val, minute_val = int(time_parts[0]), int(time_parts[1])
                if 0 <= hour_val <= 23 and 0 <= minute_val <= 59:
                    slot_time = f"{hour_val:02d}:00" if minute_val < 30 else f"{hour_val:02d}:30"
                    structured_events[event_date_iso][slot_time].append(event_struct)
                else: structured_events[event_date_iso]['all_day'].append(event_struct)
            else: structured_events[event_date_iso]['all_day'].append(event_struct)

        display_month_obj = start_d.replace(day=1)
        nav_prev_week = start_d - timedelta(days=7)
        if nav_prev_week < limit_past_date: nav_prev_week = None
        nav_next_week = start_d + timedelta(days=7)
        if (nav_next_week + timedelta(days=6)) > limit_future_date: nav_next_week = None
        header_nav_prev_month = (display_month_obj - timedelta(days=1)).replace(day=1)
        if header_nav_prev_month.replace(day=calendar.monthrange(header_nav_prev_month.year, header_nav_prev_month.month)[1]) < limit_past_date: header_nav_prev_month = None
        header_nav_next_month = (display_month_obj + timedelta(days=31)).replace(day=1)
        if header_nav_next_month > limit_future_date: header_nav_next_month = None
        return render_template("week_view.html", user=user, stats=stats, start=start_d, week_days=week_days, time_slots=time_slots,
                               structured_events=structured_events, timedelta=timedelta, view=view, month=display_month_obj,
                               today_date=today.isoformat(), nav_prev_week=nav_prev_week, nav_next_week=nav_next_week,
                               header_nav_prev_month=header_nav_prev_month, header_nav_next_month=header_nav_next_month)
    else: # month view
        target_month_display = month

        # カレンダー表示のための週データを取得 (既存のcalインスタンス作成をここに移動)
        cal = calendar.Calendar(firstweekday=0) # firstweekday=0 は月曜日始まり
        weeks_data = [w for w in cal.monthdatescalendar(target_month_display.year, target_month_display.month)]

        display_start_date = None
        display_end_date = None
        if weeks_data:
            display_start_date = weeks_data[0][0]
            display_end_date = weeks_data[-1][-1]

        # イベントのフィルタリング範囲を拡張
        events_for_display_period = []
        if display_start_date and display_end_date:
            for e_event in events: # 'events' は既にソート済みの全イベントリスト
                try:
                    event_date_obj = date.fromisoformat(e_event.get("date", ""))
                    if display_start_date <= event_date_obj <= display_end_date:
                        events_for_display_period.append(e_event)
                except ValueError:
                    continue # 不正な日付フォーマットのイベントはスキップ

        # flash(f"表示期間: {display_start_date} - {display_end_date}, イベント数: {len(events_for_display_period)}") # デバッグ用

        nav_prev_month_val = (target_month_display - timedelta(days=1)).replace(day=1)
        if nav_prev_month_val.replace(day=calendar.monthrange(nav_prev_month_val.year, nav_prev_month_val.month)[1]) < limit_past_date: nav_prev_month_val = None
        nav_next_month_val = (target_month_display + timedelta(days=31)).replace(day=1)
        if nav_next_month_val > limit_future_date: nav_next_month_val = None

        events_by_date = defaultdict(list)
        for e_event_by_date in events_for_display_period: # 修正: events_month から events_for_display_period に変更
            events_by_date[e_event_by_date["date"]].append(e_event_by_date)

        return render_template("month_view.html", events_by_date=events_by_date, user=user, stats=stats, month=target_month_display,
                               nav_prev_month=nav_prev_month_val, nav_next_month=nav_next_month_val, weeks=weeks_data, timedelta=timedelta,
                               current_month_number=target_month_display.month) # current_month_number を追加

# ... (rest of the file: /add, /edit, /delete, /move, /assign, /shift, /shift_rules, /stats, and API routes) ...
# This overwrite will ensure the rest of the file remains the same.

@bp.route("/add", methods=["GET", "POST"])
def add():
    user = session.get("user")
    form = EventForm()
    if form.validate_on_submit():
        # employee field is being removed, so don't pass it to add_event
        utils.add_event(
            event_date_obj=form.date.data, # Renamed for clarity to match util function
            title=form.title.data,
            description=form.description.data or "",
            employee='',  # employeeフィールドがないため空文字列を渡す
            category=form.category.data, # category をフォームから取得
            participants=form.participants.data, # participants をフォームから取得
            time=form.time.data # time をフォームから取得
        )
        flash("新しい予定を追加しました。", "success")
        return redirect(url_for("calendario.index"))
    # For GET request or form validation error
    return render_template("event_form.html", form=form, user=user, event_id=None) # is_edit=False is implicit by event_id=None

@bp.route("/edit/<int:event_id>", methods=["GET", "POST"])
def edit_event(event_id: int):
    user = session.get("user")
    event = utils.get_event_by_id(event_id)
    if not event:
        flash("指定されたイベントが見つかりません。", "error")
        return redirect(url_for("calendario.index"))

    # Initialize form
    if request.method == 'GET':
        # For GET, populate form with event data
        form = EventForm(data=event)
        if event.get("date"):
            try:
                form.date.data = date.fromisoformat(event["date"]) # Ensure date is a date object
            except (TypeError, ValueError):
                flash("イベントの日付形式が無効です。", "warning")
                form.date.data = None # Or some default
        if event.get("time"):
            try:
                form.time.data = datetime.strptime(event["time"], '%H:%M').time() # Convert string to time object
            except (TypeError, ValueError):
                flash("イベントの時間形式が無効です。", "warning")
                form.time.data = None # Or some default
        # Ensure participants is a list, even if not present or None in event data
        form.participants.data = event.get("participants", [])
    else:
        # For POST, create an empty form; validate_on_submit will populate it from request data
        form = EventForm()

    if form.validate_on_submit():
        if form.delete.data:  # Delete button was pressed
            if utils.delete_event(event_id):
                flash("予定を削除しました。", "success")
            else:
                flash("削除中にエラーが発生しました。", "error")
            return redirect(url_for("calendario.index"))
        else:  # Save button was pressed
            updated_event_data = {
                "date": form.date.data.isoformat(),
                "title": form.title.data,
                "description": form.description.data or "",
                # "employee": form.employee.data or "", # Employee field is being removed
                "category": form.category.data,
                "participants": form.participants.data,  # Pass as a list
                "time": form.time.data.isoformat(timespec='minutes') if form.time.data else None
            }
            if utils.update_event(event_id, updated_event_data):
                flash("予定を更新しました。", "success")
            else:
                flash("更新中にエラーが発生しました。", "error")
            return redirect(url_for("calendario.index"))

    # For GET request or form validation error, render the form
    # Pass event_id to the template for the form action URL and possibly other logic
    return render_template("event_form.html", form=form, user=user, event_id=event_id)


@bp.route("/delete/<int:event_id>") # This route might become obsolete if delete is only from edit_event form
def delete(event_id: int):
    user = session.get("user")
    # Consider admin check or other permission checks if this route is kept
    # if user.get("role") != "admin":
    #     flash("権限がありません");
    #     return redirect(url_for("calendario.index"))
    if utils.delete_event(event_id):
        flash("削除しました")
    else:
        flash("該当IDがありません")
    return redirect(url_for("calendario.index"))

@bp.route("/move/<int:event_id>", methods=["POST"])
def move(event_id: int):
    user = session.get("user"); new_date_str = request.form.get("date")
    try: new_date_obj = datetime.fromisoformat(new_date_str).date()
    except Exception: flash("日付の形式が不正です"); return redirect(url_for("calendario.index"))
    if utils.move_event(event_id, new_date_obj): flash("移動しました")
    else: flash("該当IDがありません")
    return redirect(url_for("calendario.index"))

@bp.route("/assign/<int:event_id>", methods=["POST"])
def assign(event_id: int):
    employee_val = request.form.get("employee", "") 
    if utils.assign_employee(event_id, employee_val): flash("更新しました")
    else: flash("該当IDがありません")
    return redirect(url_for("calendario.index"))

@bp.route("/shift", methods=["GET", "POST"])
def shift():
    user = session.get("user"); month_param = request.args.get("month"); today = date.today()
    if month_param:
        try: year, mon = map(int, month_param.split("-")); target_month_display = date(year, mon, 1)
        except Exception: target_month_display = date(today.year, today.month, 1)
    else: target_month_display = date(today.year, today.month, 1)
    weekday_of_first_day = target_month_display.weekday()
    start_of_first_week_in_target_month_view = target_month_display - timedelta(days=weekday_of_first_day)
    actual_calendar_start_date = start_of_first_week_in_target_month_view - timedelta(days=7)
    current_day_iterator = actual_calendar_start_date; weeks_for_display = []
    for _week_num in range(6):
        week_row = []
        for _day_in_week in range(7): week_row.append(current_day_iterator); current_day_iterator += timedelta(days=1)
        weeks_for_display.append(week_row)
    actual_calendar_end_date = weeks_for_display[-1][-1]
    fetch_data_start_date_for_calc = actual_calendar_start_date - timedelta(days=14)
    fetch_data_end_date_for_calc = actual_calendar_end_date
    if request.method == "POST":
        if not user or user.get("role") != "admin":
            flash("権限がありません (POST Auth)"); return redirect(url_for("calendario.index", month=target_month_display.strftime('%Y-%m')))
        action = request.form.get("action"); schedule: Dict[str, List[str]] = {}
        for key, val in request.form.items():
            if key.startswith("d-"): schedule[key[2:]] = [e for e in val.split(',') if e]
        try: utils.set_shift_schedule(target_month_display, schedule)
        except Exception as e: flash(f"シフトの保存中にエラーが発生しました: {e}", "error"); return redirect(url_for("calendario.shift", month=target_month_display.strftime('%Y-%m')))
        if action == "notify":
            try: utils._notify_all("シフト更新", f"{target_month_display.strftime('%Y-%m')} のシフトが更新されました"); utils.check_rules_and_notify(send_notifications=True); flash("通知を送信しました")
            except Exception as e: flash(f"通知の送信中にエラーが発生しました: {str(e)}", "error")
        elif action == "complete": flash("保存しました")
        else: flash("変更が保存されました")
        return redirect(url_for("calendario.shift", month=target_month_display.strftime('%Y-%m')))
    all_events_raw = utils.load_events()

    # Process all events (similar to index() route)
    for event in all_events_raw:
        title_match = time_title_pattern.match(event.get('title', ''))
        if title_match:
            event['display_time'] = title_match.group(1)
            event['cleaned_title'] = title_match.group(2).strip()
        else:
            event['display_time'] = None
            event['cleaned_title'] = event.get('title', '')

        category = event.get('category', 'other')
        has_time = event.get('display_time') is not None
        if category == 'shucchou':
            event['sort_priority'] = EVENT_SORT_PRIORITY['shucchou']
            event['sort_time'] = "00:00"
        elif category == 'hug':
            event['sort_priority'] = EVENT_SORT_PRIORITY['hug']
            event['sort_time'] = "00:00"
        elif category == 'shift':
            event['sort_priority'] = EVENT_SORT_PRIORITY['shift']
            event['sort_time'] = "00:00" # Shifts are typically all-day in display sense or handled by specific UI
        elif category in ['lesson', 'kouza', 'other', 'mummy', 'tattoo']:
            if has_time:
                event['sort_priority'] = EVENT_SORT_PRIORITY['other_with_time']
                event['sort_time'] = event['display_time']
            else:
                event['sort_priority'] = EVENT_SORT_PRIORITY['other_no_time']
                event['sort_time'] = "00:00"
        else: # Fallback
            event['sort_priority'] = 99
            event['sort_time'] = "23:59"

    # Filter events for the date range of the shift manager view (actual_calendar_start_date to actual_calendar_end_date)
    # And also for the extended range needed for consecutive calculation (fetch_data_start_date_for_calc to fetch_data_end_date_for_calc)

    relevant_events_for_display = []
    for event in all_events_raw:
        try:
            event_date_obj = date.fromisoformat(event.get("date", ""))
            if actual_calendar_start_date <= event_date_obj <= actual_calendar_end_date:
                relevant_events_for_display.append(event)
        except ValueError:
            continue

    relevant_events_for_display.sort(key=lambda e: (e.get("date", ""), e.get('sort_priority', 99), e.get('sort_time', '23:59')))

    all_events_by_date_for_shift_view = defaultdict(list)
    for event in relevant_events_for_display:
        all_events_by_date_for_shift_view[event["date"]].append(event)

    # Prepare shift-specific assignments for form submission and counts (original logic)
    assignments_for_form_submission: Dict[str, List[str]] = defaultdict(list)
    for event in all_events_raw: # Use all_events_raw to capture all shifts for the month for form
        if event.get("category") == "shift":
            try:
                # Check if event_date is within the visible calendar range for display consistency
                event_date_obj = date.fromisoformat(event.get("date", ""))
                if actual_calendar_start_date <= event_date_obj <= actual_calendar_end_date:
                     assignments_for_form_submission[event["date"]].append(event.get("employee", ""))
            except ValueError:
                continue

    # For consecutive day calculations, use a wider range
    assignments_for_consecutive_calc: Dict[str, List[str]] = defaultdict(list)
    for event in all_events_raw:
        if event.get("category") == "shift":
            try:
                event_date_obj = date.fromisoformat(event.get("date", ""))
                if fetch_data_start_date_for_calc <= event_date_obj <= fetch_data_end_date_for_calc:
                    assignments_for_consecutive_calc[event["date"]].append(event.get("employee", ""))
            except ValueError: continue

    employees = [n for n, info_user in config.USERS.items() if info_user.get("role") != "admin"]

    # Counts should be based on the current target_month, not the entire display or calculation range
    target_month_shifts_for_counts: Dict[str, List[str]] = defaultdict(list)
    for event in all_events_raw:
        if event.get("category") == "shift" and event.get("date", "").startswith(target_month_display.strftime("%Y-%m")):
            target_month_shifts_for_counts[event["date"]].append(event.get("employee", ""))

    counts = {emp: sum(emp in v for v in target_month_shifts_for_counts.values()) for emp in employees}
    days_in_target_month = calendar.monthrange(target_month_display.year, target_month_display.month)[1]
    off_counts = {emp: days_in_target_month - counts.get(emp, 0) for emp in employees}

    limit_past_date = today.replace(year=today.year - 2); limit_future_date = today.replace(year=today.year + 2)
    nav_prev_month_obj = (target_month_display - timedelta(days=1)).replace(day=1)
    if nav_prev_month_obj.replace(day=calendar.monthrange(nav_prev_month_obj.year, nav_prev_month_obj.month)[1]) < limit_past_date: nav_prev_month_obj = None
    nav_next_month_obj = (target_month_display + timedelta(days=31)).replace(day=1)
    if nav_next_month_obj > limit_future_date: nav_next_month_obj = None

    rules, defined_attributes = utils.load_rules(); rules_data_for_js = {"rules": rules, "defined_attributes": defined_attributes}
    csrf_form = ShiftManagementForm()
    consecutive_days_data = utils.calculate_consecutive_work_days_for_all(assignments_for_consecutive_calc, target_month_display)

    return render_template("shift_manager.html", user=user, month=target_month_display,
                           rules_for_js=rules_data_for_js, form=csrf_form,
                           weeks=weeks_for_display, employees=employees,
                           assignments=assignments_for_form_submission, # For hidden inputs
                           all_events_by_date=all_events_by_date_for_shift_view, # For display
                           counts=counts, off_counts=off_counts,
                           nav_prev_month=nav_prev_month_obj, nav_next_month=nav_next_month_obj,
                           consecutive_days_data=consecutive_days_data,
                           EVENT_SORT_PRIORITY=EVENT_SORT_PRIORITY) # Pass EVENT_SORT_PRIORITY if needed in template

@bp.route("/shift_rules", methods=["GET", "POST"])
def shift_rules():
    user = session.get("user")
    if user.get("role") != "admin": flash("権限がありません"); return redirect(url_for("calendario.index"))
    # utils.load_rules() が rules辞書と defined_attributes リストを返すと想定
    # rules辞書の中に specialized_requirements が含まれるように utils.py で修正する
    rules, defined_attributes = utils.load_rules(); form = ShiftRulesForm()
    form_employees = [n for n in config.USERS if n not in config.EXCLUDED_USERS]
    if request.method == "GET":
        form.max_consecutive_days.data = str(rules.get("max_consecutive_days", "")); form.min_staff_per_day.data = str(rules.get("min_staff_per_day", ""))
        form.forbidden_pairs.data = ",".join("-".join(p) for p in rules.get("forbidden_pairs", [])); form.required_pairs.data = ",".join("-".join(p) for p in rules.get("required_pairs", []))
        emp_attrs_items = [];_ = [emp_attrs_items.append(f"{k}:{'|'.join(v_list) if isinstance(v_list, list) else v_list}") for k, v_list in rules.get("employee_attributes", {}).items()]
        form.employee_attributes.data = ",".join(emp_attrs_items)
        req_attrs_items = [];_ = [req_attrs_items.append(f"{k}:{v_int}") for k, v_int in rules.get("required_attributes", {}).items()]
        form.required_attributes.data = ",".join(req_attrs_items)
        # specialized_requirements_json_str はGET時には設定不要（JSがinitialShiftRulesから読み込む）
    if form.validate_on_submit():
        rules_to_save = {"max_consecutive_days": int(form.max_consecutive_days.data or 0), "min_staff_per_day": int(form.min_staff_per_day.data or 0),
                         "forbidden_pairs": utils.parse_pairs(form.forbidden_pairs.data or ""), "required_pairs": utils.parse_pairs(form.required_pairs.data or ""),
                         "employee_attributes": utils.parse_kv(form.employee_attributes.data or ""), "required_attributes": utils.parse_kv_int(form.required_attributes.data or "")}

        defined_attributes_json_str = request.form.get("defined_attributes_json_str", "[]")
        try:
            submitted_defined_attributes = json.loads(defined_attributes_json_str)
            if not (isinstance(submitted_defined_attributes, list) and all(isinstance(attr, str) for attr in submitted_defined_attributes)):
                flash("属性リストの形式が不正です。", "error"); submitted_defined_attributes = utils.DEFAULT_DEFINED_ATTRIBUTES[:]
            elif not submitted_defined_attributes: 
                 flash("属性リストは空にできません。デフォルトに戻します。", "warning"); submitted_defined_attributes = utils.DEFAULT_DEFINED_ATTRIBUTES[:]
        except json.JSONDecodeError: flash("属性リストのJSON解析に失敗しました。", "error"); submitted_defined_attributes = utils.DEFAULT_DEFINED_ATTRIBUTES[:]

        specialized_requirements_to_save = {}
        specialized_json_str = form.specialized_requirements_json_str.data
        if specialized_json_str:
            try:
                specialized_requirements_to_save = json.loads(specialized_json_str)
                if not isinstance(specialized_requirements_to_save, dict):
                    flash("専門予定データの形式が不正です。既存の設定値を維持します。", "error")
                    # エラー時は既存値を維持する
                    loaded_rules_for_error, _ = utils.load_rules()
                    specialized_requirements_to_save = loaded_rules_for_error.get("specialized_requirements", {})
            except json.JSONDecodeError:
                flash("専門予定データのJSON解析に失敗しました。既存の設定値を維持します。", "error")
                loaded_rules_for_error, _ = utils.load_rules()
                specialized_requirements_to_save = loaded_rules_for_error.get("specialized_requirements", {})

        # utils.save_rules に specialized_requirements_to_save も渡す
        # utils.save_rules のシグネチャ変更を後続で行う: save_rules(rules_data, defined_attributes, specialized_requirements_data)
        utils.save_rules(rules_to_save, submitted_defined_attributes, specialized_requirements_to_save)
        flash("保存しました"); return redirect(url_for("calendario.shift_rules"))

    # JavaScriptに渡すルールデータ
    # rules_for_js の中の rules オブジェクトに specialized_requirements も含まれるようにする
    rules_for_js_payload = rules.copy() # これで specialized_requirements もコピーされる想定

    return render_template("shift_rules.html", form=form, user=user, employees=form_employees,
                           attributes=defined_attributes,
                           rules_for_js={"rules": rules_for_js_payload, "defined_attributes": defined_attributes })

@bp.route("/stats", methods=["GET", "POST"])
def stats():
    user = session.get("user"); form = StatsForm(request.values)
    start_val = form.start.data; end_val = form.end.data
    stats_data = utils.compute_employee_stats(start_date_param=start_val, end_date_param=end_val) 
    return render_template("stats.html", form=form, stats=stats_data, user=user)

@bp.route("/api/move", methods=["POST"])
def api_move() -> "flask.Response":
    data = request.get_json(silent=True) or {}; event_id_val = int(data.get("event_id", 0)); date_str_val = data.get("date", "")
    try: new_date_api = datetime.fromisoformat(date_str_val).date()
    except Exception: return jsonify({"success": False, "error": "invalid date"}), 400
    ok_status = utils.move_event(event_id_val, new_date_api); return jsonify({"success": ok_status})

@bp.route("/api/assign", methods=["POST"])
def api_assign() -> "flask.Response":
    data = request.get_json(silent=True) or {}; event_id_api = int(data.get("event_id", 0)); employee_api = data.get("employee", "")
    ok_api_status = utils.assign_employee(event_id_api, employee_api); return jsonify({"success": ok_api_status})

@bp.route("/api/shift_counts/recalculate", methods=["POST"])
def api_recalculate_shift_counts() -> "flask.Response":
    data = request.get_json(silent=True)
    if not data: return jsonify({"success": False, "error": "Invalid JSON payload"}), 400
    month_str = data.get("month"); assignments = data.get("assignments")
    if not month_str or not isinstance(month_str, str): return jsonify({"success": False, "error": "Missing or invalid month string"}), 400
    if assignments is None or not isinstance(assignments, dict): return jsonify({"success": False, "error": "Missing or invalid assignments data"}), 400
    try: year, mon = map(int, month_str.split("-")); _, days_in_month = calendar.monthrange(year, mon)
    except ValueError: return jsonify({"success": False, "error": "Invalid month format. Use YYYY-MM"}), 400
    except Exception as e: return jsonify({"success": False, "error": f"Error processing month: {str(e)}"}), 400
    try: employees = [name for name, user_info in config.USERS.items() if user_info.get("role") != "admin" and name not in config.EXCLUDED_USERS]
    except AttributeError: employees = [name for name, user_info in getattr(config, "USERS", {}).items() if user_info.get("role") != "admin" and name not in getattr(config, "EXCLUDED_USERS", [])]
    counts = {emp: 0 for emp in employees}
    for date_str, assigned_employees in assignments.items():
        if not isinstance(assigned_employees, list): continue
        for emp in assigned_employees:
            if emp in counts: counts[emp] += 1
    off_counts = {emp: days_in_month - counts.get(emp, 0) for emp in employees}
    return jsonify({ "success": True, "counts": counts, "off_counts": off_counts })

@bp.route('/api/check_shift_violations', methods=['POST'])
def check_shift_violations_api():
    payload = request.get_json()
    if not payload: return jsonify({"success": False, "error": "Invalid request data: No data received"}), 400
    current_assignments = payload.get('assignments'); target_month_str = payload.get('month')
    if current_assignments is None or not isinstance(current_assignments, dict): return jsonify({"success": False, "error": "Invalid request data: 'assignments' key missing or invalid"}), 400
    if not target_month_str or not isinstance(target_month_str, str): return jsonify({"success": False, "error": "Invalid request data: 'month' key missing or invalid"}), 400
    try: year, month_num = map(int, target_month_str.split('-')); target_month_start = date(year, month_num, 1)
    except ValueError: return jsonify({"success": False, "error": "Invalid month format. Please use YYYY-MM."}), 400
    rules, _ = utils.load_rules(); users_config = config.USERS
    violation_list = utils.get_shift_violations(current_assignments, rules, users_config)
    consecutive_info = utils.calculate_consecutive_work_days_for_all(current_assignments, target_month_start)
    return jsonify({"success": True, "violations": violation_list, "consecutive_work_info": consecutive_info})

@bp.route('/api/event/drop', methods=['POST'])
def api_event_drop():
    print(f"LOG: {datetime.now()} - Entered api_event_drop")
    data = request.get_json()
    if not data:
        print(f"LOG: {datetime.now()} - Invalid request: No payload")
        return jsonify({"success": False, "error": "無効なリクエストです。ペイロードがありません。"}), 400

    event_id_str = data.get('event_id')
    new_date_str = data.get('new_date')
    operation = data.get('operation')
    print(f"LOG: {datetime.now()} - Request data: event_id={event_id_str}, new_date={new_date_str}, operation={operation}")

    if not all([event_id_str, new_date_str, operation]):
        print(f"LOG: {datetime.now()} - Invalid request: Missing required fields")
        return jsonify({"success": False, "error": "無効なリクエストです。必須フィールドがありません。"}), 400

    try:
        event_id = int(event_id_str)
        new_date_obj = date.fromisoformat(new_date_str)
    except ValueError:
        print(f"LOG: {datetime.now()} - Invalid request: Incorrect event_id or date format")
        return jsonify({"success": False, "error": "無効なリクエストです。event_idまたは日付の形式が正しくありません。"}), 400

    print(f"LOG: {datetime.now()} - Request data validated. Event ID: {event_id}, New Date: {new_date_obj}")

    print(f"LOG: {datetime.now()} - Calling utils.get_event_by_id for event_id: {event_id}")
    original_event = utils.get_event_by_id(event_id)
    print(f"LOG: {datetime.now()} - Returned from utils.get_event_by_id. Found: {'Yes' if original_event else 'No'}")

    if not original_event:
        print(f"LOG: {datetime.now()} - Event not found for ID: {event_id}")
        return jsonify({"success": False, "error": "指定されたイベントが見つかりません。"}), 404

    try:
        if operation == "move":
            print(f"LOG: {datetime.now()} - Operation: move. Calling utils.move_event for event_id: {event_id}")
            move_success = utils.move_event(event_id, new_date_obj)
            print(f"LOG: {datetime.now()} - Returned from utils.move_event. Success: {move_success}")
            if move_success:
                print(f"LOG: {datetime.now()} - Move successful. Returning 200.")
                return jsonify({"success": True, "message": "イベントが移動されました。"}), 200
            else:
                print(f"LOG: {datetime.now()} - Move failed. Returning 500.")
                return jsonify({"success": False, "error": "イベントの移動に失敗しました。"}), 500

        elif operation == "copy":
            print(f"LOG: {datetime.now()} - Operation: copy. Original event_id: {event_id}")
            print(f"LOG: {datetime.now()} - Loading events for ID generation...")
            events = utils.load_events()
            next_id = max((e.get("id", 0) for e in events), default=0) + 1
            print(f"LOG: {datetime.now()} - New event ID generated: {next_id}")

            copied_event = original_event.copy()
            copied_event["id"] = next_id
            copied_event["date"] = new_date_obj.isoformat()

            events.append(copied_event)
            print(f"LOG: {datetime.now()} - Saving events with new copied event...")
            utils.save_events(events)
            print(f"LOG: {datetime.now()} - Events saved. Notifying for copied event...")
            utils._notify_event("add", copied_event)
            print(f"LOG: {datetime.now()} - Notification sent. Checking rules...")
            utils.check_rules_and_notify()
            print(f"LOG: {datetime.now()} - Rules checked. Copy successful. Returning 201.")
            return jsonify({"success": True, "message": "イベントがコピーされました。", "new_event_id": next_id}), 201

        else:
            print(f"LOG: {datetime.now()} - Invalid operation: {operation}. Returning 400.")
            return jsonify({"success": False, "error": "無効な操作です。"}), 400

    except Exception as e:
        print(f"LOG: {datetime.now()} - Error during event drop operation: {e}")
        # Log the exception e for debugging
        print(f"Error during event drop operation: {e}") # This is existing log, fine to keep
        return jsonify({"success": False, "error": "サーバー内部エラーが発生しました。"}), 500
