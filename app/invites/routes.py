"""Routes for invite management."""

from flask import render_template, redirect, url_for, flash, session, request

from . import bp, utils


@bp.before_request
def require_admin():
    user = session.get("user")
    if not user:
        return redirect(url_for("auth.login", next=request.url))
    if user.get("role") != "admin":
        flash("権限がありません")
        return redirect(url_for("index"))


@bp.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        utils.create_invite()
        flash("作成しました")
        return redirect(url_for("invites.index"))
    invites = utils.load_invites()
    user = session.get("user")
    return render_template("invites/invite_list.html", invites=invites, user=user)


@bp.route("/delete/<code>")
def delete(code: str):
    utils.delete_invite(code)
    flash("削除しました")
    return redirect(url_for("invites.index"))
