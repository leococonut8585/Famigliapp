"""Routes for Monsignore blueprint."""

import os
from flask import render_template, session, redirect, url_for, flash, request
from app.utils import save_uploaded_file

from . import bp
from .forms import AddMonsignoreForm, MonsignoreFilterForm
from . import utils

UPLOAD_FOLDER = os.path.join("static", "uploads")


@bp.before_request
def require_login():
    if "user" not in session:
        return redirect(url_for("auth.login", next=request.url))


@bp.route("/")
def index():
    user = session.get("user")
    form = MonsignoreFilterForm(request.args)
    posts = utils.filter_posts(
        author=form.author.data or "",
        keyword=form.keyword.data or "",
    )
    return render_template(
        "monsignore/monsignore_list.html", posts=posts, form=form, user=user
    )


@bp.route("/add", methods=["GET", "POST"])
def add():
    user = session.get("user")
    form = AddMonsignoreForm()
    if form.validate_on_submit():
        filename = None
        if form.image.data and form.image.data.filename:
            try:
                filename = save_uploaded_file(form.image.data, UPLOAD_FOLDER)
            except ValueError as e:
                flash(str(e))
                return render_template("monsignore/monsignore_form.html", form=form, user=user)
        utils.add_post(user["username"], form.body.data, filename)
        flash("投稿しました")
        return redirect(url_for("monsignore.index"))
    return render_template("monsignore/monsignore_form.html", form=form, user=user)


@bp.route("/delete/<int:post_id>")
def delete(post_id: int):
    user = session.get("user")
    if user.get("role") != "admin":
        flash("権限がありません")
        return redirect(url_for("monsignore.index"))
    if utils.delete_post(post_id):
        flash("削除しました")
    else:
        flash("該当IDがありません")
    return redirect(url_for("monsignore.index"))
