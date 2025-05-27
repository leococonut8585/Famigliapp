"""Routes for Calendario."""

from datetime import datetime

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
from .forms import EventForm, StatsForm
from . import utils


@bp.before_request
def require_login():
    if "user" not in session:
        return redirect(url_for("auth.login", next=request.url))


@bp.route("/")
def index():
    user = session.get("user")
    events = utils.load_events()
    events.sort(key=lambda e: e.get("date"))
    stats = {}
    if events:
        try:
            start = date.fromisoformat(events[0].get("date"))
        except Exception:
            start = None
        stats = utils.compute_employee_stats(start=start, end=date.today())
    return render_template(
        "event_list.html", events=events, user=user, stats=stats
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

