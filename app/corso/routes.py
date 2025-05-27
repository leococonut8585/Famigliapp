"""Routes for Corso blueprint."""

import os
from datetime import datetime
from flask import (
    render_template,
    session,
    redirect,
    url_for,
    flash,
    request,
    send_from_directory,
)
from app.utils import save_uploaded_file, send_email
import config

from . import bp
from .forms import AddCorsoForm, FeedbackForm
from app.calendario import utils as calendario_utils
from . import utils

UPLOAD_FOLDER = os.path.join("static", "uploads")


@bp.before_request
def require_login():
    if "user" not in session:
        return redirect(url_for("auth.login", next=request.url))


@bp.route("/")
def index():
    """Display list of Corso posts."""

    user = session.get("user")
    include_expired = user.get("role") == "admin"
    posts = utils.filter_posts(include_expired=include_expired)
    return render_template("corso_list.html", posts=posts, user=user)


@bp.route("/add", methods=["GET", "POST"])
def add():
    """Add a new Corso post."""

    user = session.get("user")
    form = AddCorsoForm()
    if form.validate_on_submit():
        filename = None
        if form.attachment.data and form.attachment.data.filename:
            try:
                filename = save_uploaded_file(
                    form.attachment.data,
                    UPLOAD_FOLDER,
                    utils.ALLOWED_EXTS,
                    utils.MAX_SIZE,
                )
            except ValueError as e:
                flash(str(e))
                return render_template(
                    "corso_post_form.html",
                    form=form,
                    user=user,
                    allowed_exts=", ".join(utils.ALLOWED_EXTS),
                    max_size=utils.MAX_SIZE,
                )
        utils.add_post(
            user["username"],
            form.title.data,
            form.body.data,
            form.end_date.data,
            filename,
        )
        for u in config.USERS.values():
            if u.get("email"):
                send_email("New Corso post", form.title.data, u["email"])
        flash("投稿しました")
        return redirect(url_for("corso.index"))
    return render_template(
        "corso_post_form.html",
        form=form,
        user=user,
        allowed_exts=", ".join(utils.ALLOWED_EXTS),
        max_size=utils.MAX_SIZE,
    )


@bp.route("/detail/<int:post_id>")
def detail(post_id: int):
    """Show post detail."""

    user = session.get("user")
    posts = utils.load_posts()
    post = next((p for p in posts if p.get("id") == post_id), None)
    if not post:
        flash("該当IDがありません")
        return redirect(url_for("corso.index"))
    return render_template("corso_detail.html", post=post, user=user)


@bp.route("/delete/<int:post_id>")
def delete(post_id: int):
    """Delete a post (admin only)."""

    user = session.get("user")
    if user.get("role") != "admin":
        flash("権限がありません")
        return redirect(url_for("corso.index"))
    if utils.delete_post(post_id):
        flash("削除しました")
    else:
        flash("該当IDがありません")
    return redirect(url_for("corso.index"))


@bp.route("/download/<path:filename>")
def download(filename: str):
    """Download an attached file if within valid period."""

    user = session.get("user")
    posts = utils.load_posts()
    for p in posts:
        if p.get("filename") == filename:
            end_date = p.get("end_date")
            if user.get("role") != "admin" and end_date:
                try:
                    if datetime.fromisoformat(end_date) < datetime.now():
                        flash("公開期間が終了しています")
                        return redirect(url_for("corso.index"))
                except ValueError:
                    pass
            return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
    flash("ファイルが見つかりません")
    return redirect(url_for("corso.index"))


@bp.route("/check")
def check():
    """Show schedule from Calendario."""

    user = session.get("user")
    events = calendario_utils.load_events()
    events.sort(key=lambda e: e.get("date"))
    return render_template("corso_check.html", events=events, user=user)


@bp.route("/feedback", methods=["GET", "POST"])
def feedback():
    user = session.get("user")
    posts = utils.active_posts()
    choices = [(p.get("id"), p.get("title")) for p in posts]
    form = FeedbackForm()
    form.corso_id.choices = choices
    if form.validate_on_submit():
        if len(form.body.data or "") < 300:
            flash("短すぎるね、300文字以上になるようにもう少し集中したほうが良い")
        else:
            if utils.add_feedback(form.corso_id.data, user["username"], form.body.data):
                flash("投稿しました")
                return redirect(url_for("corso.feedback"))
            flash("該当IDがありません")
    return render_template("corso_feedback_form.html", form=form, user=user)


@bp.route("/finish/<int:post_id>")
def finish(post_id: int):
    user = session.get("user")
    if user.get("role") != "admin":
        flash("権限がありません")
        return redirect(url_for("corso.detail", post_id=post_id))
    if utils.finish_post(post_id):
        flash("終了しました")
    else:
        flash("該当IDがありません")
    return redirect(url_for("corso.detail", post_id=post_id))


@bp.route("/archive")
def archive():
    user = session.get("user")
    posts = utils.archived_posts()
    return render_template("corso_archive.html", posts=posts, user=user)

