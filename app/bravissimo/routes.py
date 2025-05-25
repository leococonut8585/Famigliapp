from flask import render_template, session, redirect, url_for, flash, request

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
        category="bravissimo",
        author=form.author.data or "",
        keyword=form.keyword.data or "",
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
        utils.add_post(user["username"], "bravissimo", form.text.data)
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
