"""Routes for Posts blueprint."""

from flask import render_template, session, redirect, url_for, flash, request

from . import bp
from .forms import AddPostForm, PostFilterForm
from app import utils


@bp.before_request
def require_login():
    if "user" not in session:
        return redirect(url_for("auth.login", next=request.url))


@bp.route("/")
def index():
    """Display posts list with optional filters."""

    user = session.get("user")
    form = PostFilterForm(request.args)
    posts = utils.filter_posts(
        category=form.category.data or "",
        author=form.author.data or "",
        keyword=form.keyword.data or "",
    )
    return render_template("posts/posts_list.html", posts=posts, form=form, user=user)


@bp.route("/add", methods=["GET", "POST"])
def add():
    """Display post form and handle submission."""

    user = session.get("user")
    form = AddPostForm()
    if form.validate_on_submit():
        utils.add_post(user["username"], form.category.data or "", form.text.data)
        flash("投稿しました")
        return redirect(url_for("posts.index"))
    return render_template("posts/post_form.html", form=form, user=user)


@bp.route("/delete/<int:post_id>")
def delete(post_id: int):
    """Delete a post (admin only)."""

    user = session.get("user")
    if user["role"] != "admin":
        flash("権限がありません")
        return redirect(url_for("posts.index"))
    if utils.delete_post(post_id):
        flash("削除しました")
    else:
        flash("該当IDがありません")
    return redirect(url_for("posts.index"))
