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
from .forms import LoginForm, RegisterForm
from app.invites import utils as invite_utils
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


@bp.route("/register", methods=["GET", "POST"])
def register():
    """User registration using invite code."""

    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data
        code = form.invite.data.strip()
        if invite_utils.mark_used(code, username):
            utils.add_user(username, password, f"{username}@example.com")
            session["user"] = {"username": username, "role": "user", "email": f"{username}@example.com"}
            flash("登録しました")
            return redirect(url_for("index"))
        flash("招待コードが無効です")
    return render_template("auth/register.html", form=form)

