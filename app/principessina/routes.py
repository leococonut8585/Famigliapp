"""Routes for Principessina blueprint."""

import os
from flask import (
    render_template,
    session,
    redirect,
    url_for,
    flash,
    request,
    send_from_directory,
)
from app.utils import save_uploaded_file

from . import bp
from .forms import AddPrincipessinaForm, PrincipessinaFilterForm
from . import utils


UPLOAD_FOLDER = os.path.join("static", "uploads")


@bp.before_request
def require_login():
    if "user" not in session:
        return redirect(url_for("auth.login", next=request.url))


@bp.route("/")
def index():
    user = session.get("user")
    form = PrincipessinaFilterForm(request.args)
    posts = utils.filter_posts(
        author=form.author.data or "",
        keyword=form.keyword.data or "",
    )
    return render_template(
        "principessina/principessina_feed.html", posts=posts, form=form, user=user
    )


@bp.route("/add", methods=["GET", "POST"])
def add():
    user = session.get("user")
    form = AddPrincipessinaForm()
    if form.validate_on_submit():
        filename = None
        if form.attachment.data and form.attachment.data.filename:
            try:
                filename = save_uploaded_file(form.attachment.data, UPLOAD_FOLDER)
            except ValueError as e:
                flash(str(e))
                return render_template(
                    "principessina/principessina_post_form.html", form=form, user=user
                )
        utils.add_post(user["username"], form.body.data, filename)
        flash("投稿しました")
        return redirect(url_for("principessina.index"))
    return render_template(
        "principessina/principessina_post_form.html", form=form, user=user
    )


@bp.route("/delete/<int:post_id>")
def delete(post_id: int):
    user = session.get("user")
    if user.get("role") != "admin":
        flash("権限がありません")
        return redirect(url_for("principessina.index"))
    if utils.delete_post(post_id):
        flash("削除しました")
    else:
        flash("該当IDがありません")
    return redirect(url_for("principessina.index"))


@bp.route("/download/<path:filename>")
def download(filename: str):
    """添付ファイルのダウンロード."""

    posts = utils.load_posts()
    for p in posts:
        if p.get("filename") == filename:
            return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
    flash("ファイルが見つかりません")
    return redirect(url_for("principessina.index"))

