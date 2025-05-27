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
from .forms import AddCorsoForm, CorsoFilterForm
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
    form = CorsoFilterForm(request.args)
    include_expired = user.get("role") == "admin"
    posts = utils.filter_posts(
        author=form.author.data or "",
        keyword=form.keyword.data or "",
        include_expired=include_expired,
    )
    return render_template("corso/corso_list.html", posts=posts, form=form, user=user)


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
                return render_template("corso/corso_post_form.html", form=form, user=user)
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
    return render_template("corso/corso_post_form.html", form=form, user=user)


@bp.route("/detail/<int:post_id>")
def detail(post_id: int):
    """Show post detail."""

    user = session.get("user")
    posts = utils.load_posts()
    post = next((p for p in posts if p.get("id") == post_id), None)
    if not post:
        flash("該当IDがありません")
        return redirect(url_for("corso.index"))
    return render_template("corso/corso_detail.html", post=post, user=user)


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

