"""Routes for Calendario."""

from datetime import datetime

from flask import (
    render_template,
    session,
    redirect,
    url_for,
    flash,
    request,
)

from . import bp
from .forms import EventForm
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
    return render_template("calendario/event_list.html", events=events, user=user)


@bp.route("/add", methods=["GET", "POST"])
def add():
    user = session.get("user")
    form = EventForm()
    if form.validate_on_submit():
        utils.add_event(form.date.data, form.title.data, form.description.data or "")
        flash("追加しました")
        return redirect(url_for("calendario.index"))
    return render_template("calendario/event_form.html", form=form, user=user)


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

