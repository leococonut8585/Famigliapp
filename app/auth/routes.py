"""Routes for authentication."""

from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    session,
    request,
)

from . import bp
from .forms import LoginForm
from app import utils


@bp.route("/login", methods=["GET", "POST"])
def login():
    """Display login form and handle submissions."""

    form = LoginForm()
    if form.validate_on_submit():
        user = utils.login(form.username.data, form.password.data)
        if user:
            session["user"] = user
            flash("ログインしました")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("index"))
        flash("ユーザー名かパスワードが違います")
    return render_template("auth/login.html", form=form)


@bp.route("/logout")
def logout():
    """Log the user out."""

    session.pop("user", None)
    flash("ログアウトしました")
    return redirect(url_for("index"))

