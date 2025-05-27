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
from .forms import EditPointsForm, HistoryFilterForm
from app import utils
import config


@bp.before_request
def require_login():
    """Require user login for all Punto routes."""
    if "user" not in session:
        return redirect(url_for("auth.login", next=request.url))


@bp.route("/", methods=["GET", "POST"])
def dashboard():
    """Display points dashboard with rankings and history."""
    user = session.get("user")
    points = utils.load_points()

    # ensure pre-registered users are present
    default_users = [
        "leo",
        "lady",
        "raito",
        "hitomi",
        "sara",
        "giun",
        "nanchan",
        "hachi",
    ]
    for name in default_users:
        points.setdefault(name, {"A": 0, "O": 0})

    form = HistoryFilterForm()
    start = end = None
    username = ""
    if form.validate_on_submit():
        username = form.username.data or ""
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

    entries = utils.filter_points_history(start=start, end=end, username=username)

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
        form=form,
        entries=entries,
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


@bp.route("/rankings")
def rankings():
    """Alias of dashboard showing ranking parameters."""
    return dashboard()


@bp.route("/history", methods=["GET", "POST"])
def history():
    """Alias of dashboard showing history section."""
    return dashboard()


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

    entries = utils.load_points_history()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["timestamp", "username", "A", "O"])
    for e in entries:
        writer.writerow([
            e.get("timestamp", ""),
            e.get("username", ""),
            e.get("A", 0),
            e.get("O", 0),
        ])
    response = make_response(buf.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = (
        "attachment; filename=points_history.csv"
    )
    return response
