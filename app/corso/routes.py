"""Routes for Corso blueprint."""

import os
from flask import render_template, session, redirect, url_for, flash, request
from werkzeug.utils import secure_filename
from app.utils import allowed_file, file_size, MAX_ATTACHMENT_SIZE

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
            fname = form.attachment.data.filename
            if not allowed_file(fname):
                flash("許可されていないファイル形式です")
                return render_template("corso/corso_post_form.html", form=form, user=user)
            if file_size(form.attachment.data) > MAX_ATTACHMENT_SIZE:
                flash("ファイルサイズが大きすぎます")
                return render_template("corso/corso_post_form.html", form=form, user=user)
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            filename = secure_filename(fname)
            form.attachment.data.save(os.path.join(UPLOAD_FOLDER, filename))
        utils.add_post(
            user["username"],
            form.title.data,
            form.body.data,
            form.end_date.data,
            filename,
        )
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

