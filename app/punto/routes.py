"""Routes for Punto blueprint."""

from datetime import datetime
from typing import Dict

from flask import (
    render_template,
    session,
    redirect,
    url_for,
    flash,
    request,
)

from . import bp
from .forms import EditPointsForm
from app import utils


@bp.before_request
def require_login():
    """Require user login for all Punto routes."""
    if "user" not in session:
        return redirect(url_for("auth.login", next=request.url))


@bp.route("/")
def dashboard():
    """Display points dashboard."""
    user = session.get("user")
    points = utils.load_points()
    if user["role"] != "admin":
        p = points.get(user["username"], {"A": 0, "O": 0})
        points = {user["username"]: p}
    return render_template("punto/punto_dashboard.html", points=points, user=user)


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
    form = EditPointsForm(a=old_a, o=old_o)
    if form.validate_on_submit():
        points[username] = {"A": form.a.data, "O": form.o.data}
        utils.save_points(points)
        utils.log_points_change(username, form.a.data - old_a, form.o.data - old_o)
        flash("保存しました")
        return redirect(url_for("punto.dashboard"))

    return render_template("punto/punto_edit_form.html", form=form, username=username)
