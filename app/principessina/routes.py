"""Routes for Principessina blueprint."""

import os
from flask import (
    render_template,
    session,
    redirect,
    url_for,
    flash,
    request,
)
from werkzeug.utils import secure_filename

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
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            filename = secure_filename(form.attachment.data.filename)
            form.attachment.data.save(os.path.join(UPLOAD_FOLDER, filename))
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

