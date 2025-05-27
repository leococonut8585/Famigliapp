"""Routes for Lezzione blueprint."""

from flask import render_template, session, redirect, url_for, flash, request

from . import bp
from .forms import LessonScheduleForm, LessonFeedbackForm
from . import utils


@bp.before_request
def require_login():
    if "user" not in session:
        return redirect(url_for("auth.login", next=request.url))


@bp.route("/")
def index():
    user = session.get("user")
    entries = utils.load_entries()
    entries.sort(key=lambda e: e.get("lesson_date"))
    return render_template("lezzione_list.html", entries=entries, user=user)


@bp.route("/schedule", methods=["GET", "POST"])
def schedule():
    user = session.get("user")
    form = LessonScheduleForm()
    if form.validate_on_submit():
        utils.add_schedule(user["username"], form.date.data, form.title.data)
        flash("登録しました")
        return redirect(url_for("lezzione.index"))
    return render_template("lezzione_schedule_form.html", form=form, user=user)


@bp.route("/feedback/<int:entry_id>", methods=["GET", "POST"])
def feedback(entry_id: int):
    user = session.get("user")
    form = LessonFeedbackForm()
    if form.validate_on_submit():
        if utils.add_feedback(entry_id, form.body.data):
            flash("投稿しました")
        else:
            flash("該当IDがありません")
        return redirect(url_for("lezzione.index"))
    return render_template(
        "lezzione_feedback_form.html", form=form, user=user, entry_id=entry_id
    )

