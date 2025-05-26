from flask import render_template, session, redirect, url_for, flash, request
import os
from werkzeug.utils import secure_filename
from app.utils import allowed_file, file_size, MAX_ATTACHMENT_SIZE

UPLOAD_FOLDER = os.path.join("static", "uploads")

from . import bp
from .forms import AddBravissimoForm, BravissimoFilterForm
from app import utils


@bp.before_request
def require_login():
    if "user" not in session:
        return redirect(url_for("auth.login", next=request.url))


@bp.route("/")
def index():
    user = session.get("user")
    form = BravissimoFilterForm(request.args)
    posts = utils.filter_posts(
        author=form.author.data or "",
        keyword=form.keyword.data or "",
        target=form.target.data or "",
    )
    return render_template(
        "bravissimo/bravissimo_list.html", posts=posts, form=form, user=user
    )


@bp.route("/add", methods=["GET", "POST"])
def add():
    user = session.get("user")
    if user["role"] != "admin":
        flash("権限がありません")
        return redirect(url_for("bravissimo.index"))
    form = AddBravissimoForm()
    if form.validate_on_submit():
        filename = None
        if form.audio.data and form.audio.data.filename:
            fname = form.audio.data.filename
            if not allowed_file(fname):
                flash("許可されていないファイル形式です")
                return render_template("bravissimo/bravissimo_form.html", form=form, user=user)
            if file_size(form.audio.data) > MAX_ATTACHMENT_SIZE:
                flash("ファイルサイズが大きすぎます")
                return render_template("bravissimo/bravissimo_form.html", form=form, user=user)
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            filename = secure_filename(fname)
            form.audio.data.save(os.path.join(UPLOAD_FOLDER, filename))
        utils.add_post(
            user["username"],
            form.text.data,
            filename,
            target=form.target.data or "",
        )
        flash("投稿しました")
        return redirect(url_for("bravissimo.index"))
    return render_template("bravissimo/bravissimo_form.html", form=form, user=user)


@bp.route("/delete/<int:post_id>")
def delete(post_id: int):
    user = session.get("user")
    if user["role"] != "admin":
        flash("権限がありません")
        return redirect(url_for("bravissimo.index"))
    if utils.delete_post(post_id):
        flash("削除しました")
    else:
        flash("該当IDがありません")
    return redirect(url_for("bravissimo.index"))
