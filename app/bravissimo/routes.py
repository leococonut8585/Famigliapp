from flask import render_template, session, redirect, url_for, flash, request
import os
from app.utils import save_uploaded_file

UPLOAD_FOLDER = os.path.join("static", "uploads")

from . import bp
from .forms import AddBravissimoForm
from . import utils as bravissimo_utils

GENERAL_USERS = [
    "raito",
    "hitomi",
    "sara",
    "giun",
    "nanchan",
    "hachi",
    "kie",
    "gumi",
]


@bp.before_request
def require_login():
    if "user" not in session:
        return redirect(url_for("auth.login", next=request.url))


@bp.route("/")
def index():
    user = session.get("user")
    posts = bravissimo_utils.filter_posts()
    posts.sort(key=lambda p: p.get("timestamp", ""), reverse=True)
    return render_template(
        "bravissimo_list.html",
        posts=posts,
        user=user,
        general_users=GENERAL_USERS,
        target=None,
    )


@bp.route("/user/<target>")
def by_user(target: str):
    user = session.get("user")
    posts = bravissimo_utils.filter_posts(target=target)
    posts.sort(key=lambda p: p.get("timestamp", ""), reverse=True)
    return render_template(
        "bravissimo_list.html",
        posts=posts,
        user=user,
        general_users=GENERAL_USERS,
        target=target,
    )


@bp.route("/add", methods=["GET", "POST"])
def add():
    user = session.get("user")
    if user["role"] != "admin":
        flash("権限がありません")
        return redirect(url_for("bravissimo.index"))
    form = AddBravissimoForm()
    form.target.choices = [(u, u) for u in GENERAL_USERS]
    if form.validate_on_submit():
        filename = None
        if form.audio.data and form.audio.data.filename:
            try:
                bravissimo_utils.validate_audio(form.audio.data)
                filename = save_uploaded_file(
                    form.audio.data,
                    UPLOAD_FOLDER,
                    allowed_exts={"mp3", "wav"},
                )
            except ValueError as e:
                flash(str(e))
                return render_template("bravissimo_form.html", form=form, user=user)
        bravissimo_utils.add_post(
            user["username"],
            filename,
            target=form.target.data,
        )
        flash("投稿しました")
        return redirect(url_for("bravissimo.index"))
    return render_template("bravissimo_form.html", form=form, user=user)


@bp.route("/delete/<int:post_id>")
def delete(post_id: int):
    user = session.get("user")
    if user["role"] != "admin":
        flash("権限がありません")
        return redirect(url_for("bravissimo.index"))
    if bravissimo_utils.delete_post(post_id):
        flash("削除しました")
    else:
        flash("該当IDがありません")
    return redirect(url_for("bravissimo.index"))
