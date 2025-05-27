"""Routes for Calendario."""

from datetime import datetime, date, timedelta
import calendar

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

    # ensure week starts on Monday of the given date
    week_start = week_start - timedelta(days=week_start.weekday())

    events = utils.load_events()
    events.sort(key=lambda e: e.get("date"))
    stats = {}
    if events:
        try:
            start = date.fromisoformat(events[0].get("date"))
        except Exception:
            start = None
        stats = utils.compute_employee_stats(start=start, end=date.today())

    if view == "week":
        start_d = week_start
        end_d = week_start + timedelta(days=6)
        week_events = [
            e
            for e in events
            if start_d <= date.fromisoformat(e.get("date")) <= end_d
        ]
        return render_template(
            "week_view.html",
            events=week_events,
            user=user,
            stats=stats,
            start=start_d,
            timedelta=timedelta,
        )

    else:
        # month view
        events_month = [
            e for e in events if e.get("date", "").startswith(month.strftime("%Y-%m"))
        ]
        prev_month = (month - timedelta(days=1)).replace(day=1)
        next_month = (month + timedelta(days=31)).replace(day=1)
        events_by_date = {}
        for e in events_month:
            events_by_date.setdefault(e["date"], []).append(e)
        cal = calendar.Calendar(firstweekday=0)
        weeks = []
        for w in cal.monthdatescalendar(month.year, month.month):
            weeks.append([d for d in w])
        return render_template(
            "month_view.html",
            events_by_date=events_by_date,
            user=user,
            stats=stats,
            month=month,
            prev_month=prev_month,
            next_month=next_month,
            weeks=weeks,
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
    return render_template("event_form.html", form=form, user=user)


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
        new_date = datetime.fromisoformat(new_date_str).date()
    except Exception:
        flash("日付の形式が不正です")
        return redirect(url_for("calendario.index"))
    if utils.move_event(event_id, new_date):
        flash("移動しました")
    else:
        flash("該当IDがありません")
    return redirect(url_for("calendario.index"))


@bp.route("/assign/<int:event_id>", methods=["POST"])
def assign(event_id: int):
    employee = request.form.get("employee", "")
    if utils.assign_employee(event_id, employee):
        flash("更新しました")
    else:
        flash("該当IDがありません")
    return redirect(url_for("calendario.index"))


@bp.route("/shift", methods=["GET", "POST"])
def shift():
    user = session.get("user")
    if user.get("role") != "admin":
        flash("権限がありません")
        return redirect(url_for("calendario.index"))

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

    events = utils.load_events()
    assignments: Dict[str, List[str]] = {}
    for e in events:
        if (
            e.get("category") == "shift"
            and e.get("date", "").startswith(month.strftime("%Y-%m"))
        ):
            assignments.setdefault(e["date"], []).append(e.get("employee", ""))

    employees = [n for n, info in config.USERS.items() if info.get("role") != "admin"]
    counts = {emp: sum(emp in v for v in assignments.values()) for emp in employees}
    days_in_month = calendar.monthrange(month.year, month.month)[1]
    off_counts = {emp: days_in_month - counts.get(emp, 0) for emp in employees}

    if request.method == "POST":
        action = request.form.get("action")
        schedule: Dict[str, List[str]] = {}
        for key in request.form:
            if key.startswith("d-"):
                schedule[key[2:]] = request.form.getlist(key)
        utils.set_shift_schedule(month, schedule)
        if action == "notify":
            utils._notify_all("シフト更新", f"{month.strftime('%Y-%m')} のシフトが更新されました")
            flash("通知を送信しました")
        else:
            flash("保存しました")
        return redirect(url_for("calendario.shift", month=month.strftime('%Y-%m')))

    cal = calendar.Calendar(firstweekday=0)
    weeks = [w for w in cal.monthdatescalendar(month.year, month.month)]
    prev_month = (month - timedelta(days=1)).replace(day=1)
    next_month = (month + timedelta(days=31)).replace(day=1)

    return render_template(
        "shift_manager.html",
        user=user,
        month=month,
        weeks=weeks,
        employees=employees,
        assignments=assignments,
        counts=counts,
        off_counts=off_counts,
        prev_month=prev_month,
        next_month=next_month,
    )


@bp.route("/shift_rules", methods=["GET", "POST"])
def shift_rules():
    user = session.get("user")
    if user.get("role") != "admin":
        flash("権限がありません")
        return redirect(url_for("calendario.index"))

    rules = utils.load_rules()
    form = ShiftRulesForm()
    employees = [n for n in config.USERS if n not in config.EXCLUDED_USERS]
    attributes = ["Dog", "Lady", "Man", "Kaji", "Massage"]
    if request.method == "GET":
        form.max_consecutive_days.data = str(rules.get("max_consecutive_days", ""))
        form.min_staff_per_day.data = str(rules.get("min_staff_per_day", ""))
        form.forbidden_pairs.data = ",".join("-".join(p) for p in rules.get("forbidden_pairs", []))
        form.required_pairs.data = ",".join("-".join(p) for p in rules.get("required_pairs", []))
        form.employee_attributes.data = ",".join(f"{k}:{v}" for k, v in rules.get("employee_attributes", {}).items())
        form.required_attributes.data = ",".join(f"{k}:{v}" for k, v in rules.get("required_attributes", {}).items())
    if form.validate_on_submit():
        rules["max_consecutive_days"] = int(form.max_consecutive_days.data or 0)
        rules["min_staff_per_day"] = int(form.min_staff_per_day.data or 0)
        rules["forbidden_pairs"] = utils.parse_pairs(form.forbidden_pairs.data or "")
        rules["required_pairs"] = utils.parse_pairs(form.required_pairs.data or "")
        rules["employee_attributes"] = utils.parse_kv(form.employee_attributes.data or "")
        rules["required_attributes"] = utils.parse_kv_int(form.required_attributes.data or "")
        utils.save_rules(rules)
        flash("保存しました")
        return redirect(url_for("calendario.shift_rules"))

    return render_template(
        "shift_rules.html",
        form=form,
        user=user,
        employees=employees,
        attributes=attributes,
    )


@bp.route("/stats", methods=["GET", "POST"])
def stats():
    """Show work/off day statistics for employees."""

    user = session.get("user")
    form = StatsForm(request.values)
    start = form.start.data
    end = form.end.data
    stats = utils.compute_employee_stats(start=start, end=end)
    return render_template(
        "stats.html",
        form=form,
        stats=stats,
        user=user,
    )


@bp.route("/api/move", methods=["POST"])
def api_move() -> "flask.Response":
    """Move event via JSON request."""
    data = request.get_json(silent=True) or {}
    event_id = int(data.get("event_id", 0))
    date_str = data.get("date", "")
    try:
        new_date = datetime.fromisoformat(date_str).date()
    except Exception:
        return jsonify({"success": False, "error": "invalid date"}), 400
    ok = utils.move_event(event_id, new_date)
    return jsonify({"success": ok})


@bp.route("/api/assign", methods=["POST"])
def api_assign() -> "flask.Response":
    """Assign employee via JSON request."""
    data = request.get_json(silent=True) or {}
    event_id = int(data.get("event_id", 0))
    employee = data.get("employee", "")
    ok = utils.assign_employee(event_id, employee)
    return jsonify({"success": ok})

