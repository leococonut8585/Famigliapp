"""Routes for Punto blueprint."""


from flask import (
    render_template,
    session,
    redirect,
    url_for,
    flash,
    request,
    make_response,
)
from datetime import datetime
import csv
import io

from . import bp
from .forms import EditPointsForm, HistoryFilterForm, ConsumptionAddForm
from app import utils
import config

# Names of general (non-admin) users shown in the UI
GENERAL_USERS = [
    "raito",
    "hitomi",
    "sara",
    "giun",
    "nanchan",
    "hachi",
    "kie",
    "gumi",
]


@bp.before_request
def require_login():
    """Require user login for all Punto routes."""
    if "user" not in session:
        return redirect(url_for("auth.login", next=request.url))


@bp.route("/", methods=["GET"])
def dashboard():
    """Display points dashboard with rankings."""
    user = session.get("user")
    points = utils.load_points()

    # ensure pre-registered users are present
    for name in GENERAL_USERS:
        points.setdefault(name, {"A": 0, "O": 0})

    # remove admin accounts from the display list
    points = {
        name: vals
        for name, vals in points.items()
        if config.USERS.get(name, {}).get("role") != "admin"
    }

    metric = request.args.get("metric", "U").upper()
    period = request.args.get("period", "all").lower()
    if metric not in {"A", "O", "U"}:
        metric = "U"
    if period not in {"all", "weekly", "monthly", "yearly"}:
        period = "all"
    ranking = utils.get_ranking(metric, period=None if period == "all" else period)

    if user["role"] != "admin":
        p = points.get(user["username"], {"A": 0, "O": 0})
        points = {user["username"]: p}
    return render_template(
        "punto_dashboard.html",
        points=points,
        user=user,
        ranking=ranking,
        metric=metric,
        period=period,
    )


@bp.route("/edit/<username>", methods=["GET", "POST"])
def edit(username: str):
    """Edit points for a specific user (admin only)."""
    user = session.get("user")
    if user["role"] != "admin":
        flash("権限がありません")
        return redirect(url_for("punto.dashboard"))

    points = utils.load_points()
    old_a = points.get(username, {}).get("A", 0)
    old_o = points.get(username, {}).get("O", 0)
    form = EditPointsForm(a=old_a, o=old_o, u=old_a - old_o)
    if form.validate_on_submit():
        points[username] = {"A": form.a.data, "O": form.o.data}
        utils.save_points(points)
        utils.log_points_change(username, form.a.data - old_a, form.o.data - old_o)
        flash("保存しました")
        return redirect(url_for("punto.dashboard"))

    form.u.data = form.a.data - form.o.data
    return render_template("punto_edit_form.html", form=form, username=username)


@bp.route("/adjust/<username>/<metric>/<int:delta>")
def adjust(username: str, metric: str, delta: int):
    """Increment or decrement user's points (admin only)."""
    user = session.get("user")
    if user["role"] != "admin":
        flash("権限がありません")
        return redirect(url_for("punto.dashboard"))

    if metric not in {"A", "O"}:
        flash("不正な操作です")
        return redirect(url_for("punto.dashboard"))

    points = utils.load_points()
    current = points.get(username, {"A": 0, "O": 0})
    current[metric] = current.get(metric, 0) + delta
    points[username] = current
    utils.save_points(points)
    utils.log_points_change(username, delta if metric == "A" else 0, delta if metric == "O" else 0)
    return redirect(url_for("punto.dashboard"))


@bp.route("/set/<username>", methods=["POST"])
def set_points(username: str):
    """Set points directly for a user (admin only)."""
    user = session.get("user")
    if user["role"] != "admin":
        flash("権限がありません")
        return redirect(url_for("punto.dashboard"))

    try:
        a = int(request.form.get("a", ""))
        o = int(request.form.get("o", ""))
    except ValueError:
        flash("数値を入力してください")
        return redirect(url_for("punto.dashboard"))

    points = utils.load_points()
    old_a = points.get(username, {}).get("A", 0)
    old_o = points.get(username, {}).get("O", 0)
    points[username] = {"A": a, "O": o}
    utils.save_points(points)
    utils.log_points_change(username, a - old_a, o - old_o)
    flash("保存しました")
    return redirect(url_for("punto.dashboard"))


@bp.route("/rankings")
def rankings():
    """Alias of dashboard showing ranking parameters."""
    return dashboard()


@bp.route("/history", methods=["GET", "POST"])
def history():
    """Display simple points consumption history."""

    user = session.get("user")
    form = ConsumptionAddForm()
    if user["role"] == "admin" and form.validate_on_submit():
        utils.add_points_consumption(form.username.data, form.reason.data)
        email = config.USERS.get(form.username.data, {}).get("email")
        if email:
            utils.send_email("ポイント消費が追加されました", form.reason.data, email)
        flash("追加しました")
        return redirect(url_for("punto.history"))

    entries = utils.load_points_consumption()
    entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return render_template(
        "punto_consumption_history.html",
        entries=entries,
        user=user,
        form=form,
        general_users=GENERAL_USERS,
    )


@bp.route("/graph", methods=["GET", "POST"])
def graph():
    """Display graph of points history."""

    user = session.get("user")
    form = HistoryFilterForm()
    start = end = None
    if form.validate_on_submit():
        if form.start.data:
            try:
                start = datetime.strptime(form.start.data, "%Y-%m-%d")
            except ValueError:
                flash("開始日の形式が正しくありません")
        if form.end.data:
            try:
                end = datetime.strptime(form.end.data, "%Y-%m-%d")
            except ValueError:
                flash("終了日の形式が正しくありません")

    data = utils.get_points_history_summary(start=start, end=end)

    return render_template(
        "punto_graph.html",
        form=form,
        labels=data["labels"],
        a_data=data["A"],
        o_data=data["O"],
        user=user,
    )


@bp.route("/history/export")
def export_history_csv():
    """ポイント履歴をCSVダウンロードする。管理者専用。"""

    user = session.get("user")
    if user.get("role") != "admin":
        flash("権限がありません")
        return redirect(url_for("punto.history"))

    entries = utils.load_points_consumption()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["timestamp", "username", "reason"])
    for e in entries:
        writer.writerow([
            e.get("timestamp", ""),
            e.get("username", ""),
            e.get("reason", ""),
        ])
    response = make_response(buf.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = (
        "attachment; filename=points_consumption.csv"
    )
    return response
