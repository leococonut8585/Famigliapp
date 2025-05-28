"""Routes for Calendario."""

from datetime import datetime, date, timedelta
import calendar

import json # Add for parsing defined_attributes_json_str
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
from .forms import EventForm, StatsForm, ShiftRulesForm
from . import utils
import config
from typing import Dict, List
import re # Moved from inside index()
from collections import defaultdict # Moved from inside index()


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
        if month_param:
            year, mon = map(int, month_param.split("-"))
            month = date(year, mon, 1)
        else:
            month = date(today.year, today.month, 1)
    except Exception:
        month = date(today.year, today.month, 1)

    if week_param:
        try:
            week_start = datetime.fromisoformat(week_param).date()
        except Exception:
            week_start = today - timedelta(days=today.weekday())
    else:
        week_start = today - timedelta(days=today.weekday())

    week_start = week_start - timedelta(days=week_start.weekday())

    events = utils.load_events()
    events.sort(key=lambda e: e.get("date"))
    stats = {}
    if events:
        try:
            start_date = date.fromisoformat(events[0].get("date"))
        except Exception:
            start_date = None
        # CORRECTED VERSION FOR index()
        stats = utils.compute_employee_stats(start_date_param=start_date, end_date_param=date.today())

    if view == "week":
        start_d = week_start
        end_d = week_start + timedelta(days=6)
        
        week_days = [start_d + timedelta(days=i) for i in range(7)]
        
        time_slots = []
        for hour in range(24):
            time_slots.append(f"{hour:02d}:00")
            time_slots.append(f"{hour:02d}:30")

        raw_week_events = [
            e
            for e in events
            if start_d <= date.fromisoformat(e.get("date")) <= end_d
        ]

        structured_events = defaultdict(lambda: defaultdict(list))
        time_regex = re.compile(r"(\d{1,2}):(\d{2})")

        for event in raw_week_events:
            event_date_iso = event.get("date")
            event_title = event.get("title", "")
            
            match = time_regex.search(event_title)
            if match:
                hour_val = int(match.group(1))
                minute_val = int(match.group(2))
                if 0 <= hour_val <= 23 and 0 <= minute_val <= 59:
                    if minute_val < 30:
                        slot_time = f"{hour_val:02d}:00"
                    else:
                        slot_time = f"{hour_val:02d}:30"
                    structured_events[event_date_iso][slot_time].append(event)
                else: 
                    structured_events[event_date_iso]['all_day'].append(event)
            else:
                structured_events[event_date_iso]['all_day'].append(event)
        
        display_month = start_d.replace(day=1)
        
        nav_prev_week = start_d - timedelta(days=7)
        if nav_prev_week < limit_past_date:
            nav_prev_week = None
        
        nav_next_week = start_d + timedelta(days=7)
        if (nav_next_week + timedelta(days=6)) > limit_future_date:
            nav_next_week = None

        header_nav_prev_month = (display_month - timedelta(days=1)).replace(day=1)
        if header_nav_prev_month.replace(day=calendar.monthrange(header_nav_prev_month.year, header_nav_prev_month.month)[1]) < limit_past_date:
            header_nav_prev_month = None
        
        header_nav_next_month = (display_month + timedelta(days=31)).replace(day=1)
        if header_nav_next_month > limit_future_date: 
            header_nav_next_month = None

        return render_template(
            "week_view.html",
            user=user,
            stats=stats,
            start=start_d, 
            week_days=week_days, 
            time_slots=time_slots, 
            structured_events=structured_events, 
            timedelta=timedelta,
            view=view, 
            month=display_month, 
            today_date=today.isoformat(), 
            nav_prev_week=nav_prev_week, 
            nav_next_week=nav_next_week, 
            header_nav_prev_month=header_nav_prev_month, 
            header_nav_next_month=header_nav_next_month, 
        )

    else: # month view
        events_month = [
            e for e in events if e.get("date", "").startswith(month.strftime("%Y-%m"))
        ]
        
        nav_prev_month_val = (month - timedelta(days=1)).replace(day=1)
        if nav_prev_month_val.replace(day=calendar.monthrange(nav_prev_month_val.year, nav_prev_month_val.month)[1]) < limit_past_date:
            nav_prev_month_val = None
            
        nav_next_month_val = (month + timedelta(days=31)).replace(day=1)
        if nav_next_month_val > limit_future_date:
            nav_next_month_val = None
            
        events_by_date = {}
        for e_event_by_date in events_month: 
            events_by_date.setdefault(e_event_by_date["date"], []).append(e_event_by_date)
        cal = calendar.Calendar(firstweekday=0)
        weeks_data = [] 
        for w_week_data in cal.monthdatescalendar(month.year, month.month): 
            weeks_data.append([d_day_data for d_day_data in w_week_data]) 
        return render_template(
            "month_view.html",
            events_by_date=events_by_date,
            user=user,
            stats=stats,
            month=month, 
            nav_prev_month=nav_prev_month_val, 
            nav_next_month=nav_next_month_val, 
            weeks=weeks_data, 
            timedelta=timedelta,
        )


@bp.route("/add", methods=["GET", "POST"])
def add():
    user = session.get("user")
    form = EventForm()
    if form.validate_on_submit():
        utils.add_event(
            form.date.data,
            form.title.data,
            form.description.data or "",
            form.employee.data or "",
            form.category.data,
            form.participants.data,
        )
        flash("追加しました")
        return redirect(url_for("calendario.index"))
    return render_template("event_form.html", form=form, user=user, is_edit=False, event_id=None)


@bp.route("/edit/<int:event_id>", methods=["GET", "POST"])
def edit_event(event_id: int):
    user = session.get("user") 
    event = utils.get_event_by_id(event_id)

    if not event:
        flash("指定されたイベントが見つかりません。", "error")
        return redirect(url_for("calendario.index"))

    form = EventForm()

    if request.method == "POST":
        if form.validate_on_submit():
            new_event_data = {
                "date": form.date.data.isoformat(),
                "title": form.title.data,
                "description": form.description.data or "",
                "employee": form.employee.data or "",
                "category": form.category.data,
                "participants": form.participants.data or [],
            }
            if utils.update_event(event_id, new_event_data):
                flash("イベントが更新されました。", "success")
            else:
                flash("イベントの更新に失敗しました。", "error")
            return redirect(url_for("calendario.index"))
        else: 
            flash("フォームの入力内容に誤りがあります。確認してください。", "warning")
            return render_template("event_form.html", form=form, user=user, is_edit=True, event_id=event_id)

    form.date.data = date.fromisoformat(event["date"])
    form.title.data = event["title"]
    form.description.data = event.get("description", "")
    form.employee.data = event.get("employee", "")
    form.category.data = event.get("category", "other") 
    form.participants.data = event.get("participants", [])
    
    return render_template("event_form.html", form=form, user=user, is_edit=True, event_id=event_id)


@bp.route("/delete/<int:event_id>")
def delete(event_id: int):
    user = session.get("user")
    if user.get("role") != "admin":
        flash("権限がありません")
        return redirect(url_for("calendario.index"))
    if utils.delete_event(event_id):
        flash("削除しました")
    else:
        flash("該当IDがありません")
    return redirect(url_for("calendario.index"))


@bp.route("/move/<int:event_id>", methods=["POST"])
def move(event_id: int):
    user = session.get("user")
    new_date_str = request.form.get("date")
    try:
        new_date_obj = datetime.fromisoformat(new_date_str).date() 
    except Exception:
        flash("日付の形式が不正です")
        return redirect(url_for("calendario.index"))
    if utils.move_event(event_id, new_date_obj): 
        flash("移動しました")
    else:
        flash("該当IDがありません")
    return redirect(url_for("calendario.index"))


@bp.route("/assign/<int:event_id>", methods=["POST"])
def assign(event_id: int):
    employee_val = request.form.get("employee", "") 
    if utils.assign_employee(event_id, employee_val): 
        flash("更新しました")
    else:
        flash("該当IDがありません")
    return redirect(url_for("calendario.index"))


@bp.route("/shift", methods=["GET", "POST"])
def shift():
    user = session.get("user") 

    month_param = request.args.get("month")
    today = date.today()
    if month_param:
        try:
            year, mon = map(int, month_param.split("-"))
            month = date(year, mon, 1)
        except Exception:
            month = date(today.year, today.month, 1)
    else:
        month = date(today.year, today.month, 1)

    if request.method == "POST":
        # The logging print statements from previous subtasks were here.
        # They are removed now as per this overwrite, which is fine.
        if not user or user.get("role") != "admin":
            flash("権限がありません (POST Auth)") 
            return redirect(url_for("calendario.index", month=month.strftime('%Y-%m')))

        action = request.form.get("action")
        schedule: Dict[str, List[str]] = {}
        for key, val in request.form.items():
            if key.startswith("d-"):
                emps = [e for e in val.split(',') if e]
                schedule[key[2:]] = emps
        
        try:
            utils.set_shift_schedule(month, schedule)
        except Exception as e:
            flash(f"シフトの保存中にエラーが発生しました: {e}", "error")
            return redirect(url_for("calendario.shift", month=month.strftime('%Y-%m')))

        if action == "notify":
            try:
                utils._notify_all("シフト更新", f"{month.strftime('%Y-%m')} のシフトが更新されました")
                flash("通知を送信しました")
            except Exception as e:
                # Log the exception e
                flash(f"通知の送信に失敗しました: {str(e)}", "error")
        elif action == "complete":
            flash("保存しました")
        else: # Default case for any other action, or if action is None
            flash("変更が保存されました") # Slightly different message for clarity if needed
        
        return redirect(url_for("calendario.shift", month=month.strftime('%Y-%m')))

    events = utils.load_events()
    assignments: Dict[str, List[str]] = {}
    for e_event in events: 
        if (
            e_event.get("category") == "shift"
            and e_event.get("date", "").startswith(month.strftime("%Y-%m"))
        ):
            assignments.setdefault(e_event["date"], []).append(e_event.get("employee", ""))

    employees = [n for n, info_user in config.USERS.items() if info_user.get("role") != "admin"] 
    counts = {emp: sum(emp in v for v in assignments.values()) for emp in employees}
    
    days_in_month = calendar.monthrange(month.year, month.month)[1]
    off_counts = {emp: days_in_month - counts.get(emp, 0) for emp in employees}

    cal = calendar.Calendar(firstweekday=0)
    weeks = [w for w in cal.monthdatescalendar(month.year, month.month)]

    limit_past_date = today.replace(year=today.year - 2)
    limit_future_date = today.replace(year=today.year + 2)

    nav_prev_month = (month - timedelta(days=1)).replace(day=1)
    if nav_prev_month.replace(day=calendar.monthrange(nav_prev_month.year, nav_prev_month.month)[1]) < limit_past_date:
        nav_prev_month = None
        
    nav_next_month = (month + timedelta(days=31)).replace(day=1)
    if nav_next_month > limit_future_date:
        nav_next_month = None

    return render_template(
        "shift_manager.html",
        user=user,
        month=month, 
        weeks=weeks,
        employees=employees,
        assignments=assignments, 
        counts=counts,
        off_counts=off_counts,
        nav_prev_month=nav_prev_month, 
        nav_next_month=nav_next_month, 
    )


@bp.route("/shift_rules", methods=["GET", "POST"])
def shift_rules():
    user = session.get("user")
    if user.get("role") != "admin":
        flash("権限がありません")
        return redirect(url_for("calendario.index"))

    rules, defined_attributes = utils.load_rules() 
    form = ShiftRulesForm()
    form_employees = [n for n in config.USERS if n not in config.EXCLUDED_USERS] 
    
    if request.method == "GET":
        form.max_consecutive_days.data = str(rules.get("max_consecutive_days", ""))
        form.min_staff_per_day.data = str(rules.get("min_staff_per_day", ""))
        form.forbidden_pairs.data = ",".join("-".join(p) for p in rules.get("forbidden_pairs", []))
        form.required_pairs.data = ",".join("-".join(p) for p in rules.get("required_pairs", []))
        emp_attrs_items = []
        for k, v_list in rules.get("employee_attributes", {}).items():
            if isinstance(v_list, list):
                emp_attrs_items.append(f"{k}:{ '|'.join(v_list) }")
            else: 
                emp_attrs_items.append(f"{k}:{v_list}")
        form.employee_attributes.data = ",".join(emp_attrs_items)
        
        req_attrs_items = []
        for k, v_int in rules.get("required_attributes", {}).items():
             req_attrs_items.append(f"{k}:{v_int}")
        form.required_attributes.data = ",".join(req_attrs_items)

    if form.validate_on_submit():
        rules_to_save = {} 
        rules_to_save["max_consecutive_days"] = int(form.max_consecutive_days.data or 0)
        rules_to_save["min_staff_per_day"] = int(form.min_staff_per_day.data or 0)
        rules_to_save["forbidden_pairs"] = utils.parse_pairs(form.forbidden_pairs.data or "")
        rules_to_save["required_pairs"] = utils.parse_pairs(form.required_pairs.data or "")
        rules_to_save["employee_attributes"] = utils.parse_kv(form.employee_attributes.data or "")
        rules_to_save["required_attributes"] = utils.parse_kv_int(form.required_attributes.data or "")
        
        defined_attributes_json_str = request.form.get("defined_attributes_json_str", "[]")
        try:
            submitted_defined_attributes = json.loads(defined_attributes_json_str)
            if not isinstance(submitted_defined_attributes, list) or \
               not all(isinstance(attr, str) for attr in submitted_defined_attributes):
                flash("属性リストの形式が不正です。", "error")
                submitted_defined_attributes = utils.DEFAULT_DEFINED_ATTRIBUTES[:] 
            elif not submitted_defined_attributes: 
                 flash("属性リストは空にできません。デフォルトに戻します。", "warning")
                 submitted_defined_attributes = utils.DEFAULT_DEFINED_ATTRIBUTES[:] 
        except json.JSONDecodeError:
            flash("属性リストのJSON解析に失敗しました。", "error")
            submitted_defined_attributes = utils.DEFAULT_DEFINED_ATTRIBUTES[:] 
            
        utils.save_rules(rules_to_save, submitted_defined_attributes)
        flash("保存しました")
        return redirect(url_for("calendario.shift_rules"))

    return render_template(
        "shift_rules.html",
        form=form,
        user=user,
        employees=form_employees, 
        attributes=defined_attributes, 
    )


@bp.route("/stats", methods=["GET", "POST"])
def stats():
    user = session.get("user")
    form = StatsForm(request.values)
    start_val = form.start.data 
    end_val = form.end.data 
    # CORRECTED VERSION FOR stats()
    stats_data = utils.compute_employee_stats(start_date_param=start_val, end_date_param=end_val) 
    return render_template(
        "stats.html",
        form=form,
        stats=stats_data, 
        user=user,
    )


@bp.route("/api/move", methods=["POST"])
def api_move() -> "flask.Response":
    data = request.get_json(silent=True) or {}
    event_id_val = int(data.get("event_id", 0)) 
    date_str_val = data.get("date", "") 
    try:
        new_date_api = datetime.fromisoformat(date_str_val).date() 
    except Exception:
        return jsonify({"success": False, "error": "invalid date"}), 400
    ok_status = utils.move_event(event_id_val, new_date_api) 
    return jsonify({"success": ok_status}) 


@bp.route("/api/assign", methods=["POST"])
def api_assign() -> "flask.Response":
    data = request.get_json(silent=True) or {}
    event_id_api = int(data.get("event_id", 0)) 
    employee_api = data.get("employee", "") 
    ok_api_status = utils.assign_employee(event_id_api, employee_api) 
    return jsonify({"success": ok_api_status})


@bp.route("/api/calendario/recalculate_shift_counts", methods=["POST"])
def api_recalculate_shift_counts() -> "flask.Response":
    """
    Recalculates shift counts based on provided assignments without saving.
    Expects a JSON payload like:
    {
        "month": "YYYY-MM",
        "assignments": {
            "YYYY-MM-DD": ["employeeA", "employeeB"],
            ...
        }
    }
    Returns:
    {
        "success": True,
        "counts": {"employeeA": 10, ...},
        "off_counts": {"employeeA": 15, ...}
    }
    or {"success": False, "error": "description"}
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "Invalid JSON payload"}), 400

    month_str = data.get("month")
    assignments = data.get("assignments")

    if not month_str or not isinstance(month_str, str):
        return jsonify({"success": False, "error": "Missing or invalid month string"}), 400
    
    if assignments is None or not isinstance(assignments, dict): # Allow empty assignments
        return jsonify({"success": False, "error": "Missing or invalid assignments data"}), 400

    try:
        year, mon = map(int, month_str.split("-"))
        current_month_date = date(year, mon, 1)
        _, days_in_month = calendar.monthrange(year, mon)
    except ValueError:
        return jsonify({"success": False, "error": "Invalid month format. Use YYYY-MM"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Error processing month: {str(e)}"}), 400

    # Get non-admin employees
    try:
        employees = [
            name
            for name, user_info in config.USERS.items()
            if user_info.get("role") != "admin" and name not in config.EXCLUDED_USERS
        ]
    except AttributeError: # Handle cases where USERS or EXCLUDED_USERS might not be structured as expected
        employees = [
            name
            for name, user_info in getattr(config, "USERS", {}).items()
            if user_info.get("role") != "admin" and name not in getattr(config, "EXCLUDED_USERS", [])
        ]


    counts = {emp: 0 for emp in employees}

    for date_str, assigned_employees in assignments.items():
        # Validate date_str format if necessary, though not strictly required by problem
        # For now, assume dates in assignments are for the correct month
        # and are valid date strings.
        if not isinstance(assigned_employees, list):
            # If a specific date's assignments are malformed, we can skip it or error out.
            # For now, let's be lenient and skip.
            continue
        for emp in assigned_employees:
            if emp in counts:
                counts[emp] += 1
    
    off_counts = {emp: days_in_month - counts.get(emp, 0) for emp in employees}

    return jsonify({
        "success": True,
        "counts": counts,
        "off_counts": off_counts
    })
