"""Routes for Quest Box blueprint."""

from flask import (
    render_template,
    session,
    redirect,
    url_for,
    flash,
    request,
)

from . import bp
from .forms import QuestForm, RewardForm
from . import utils


@bp.before_request
def require_login():
    if "user" not in session:
        return redirect(url_for("auth.login", next=request.url))


@bp.route("/")
def index():
    user = session.get("user")
    quests = utils.load_quests()
    return render_template("quest_box/quest_list.html", quests=quests, user=user)


@bp.route("/add", methods=["GET", "POST"])
def add():
    user = session.get("user")
    form = QuestForm()
    if form.validate_on_submit():
        utils.add_quest(user["username"], form.title.data, form.body.data, form.due_date.data)
        flash("投稿しました")
        return redirect(url_for("quest_box.index"))
    return render_template("quest_box/quest_create_form.html", form=form, user=user)


@bp.route("/detail/<int:quest_id>")
def detail(quest_id: int):
    user = session.get("user")
    quests = utils.load_quests()
    quest = next((q for q in quests if q.get("id") == quest_id), None)
    if not quest:
        flash("該当IDがありません")
        return redirect(url_for("quest_box.index"))
    return render_template("quest_box/quest_detail.html", quest=quest, user=user)


@bp.route("/accept/<int:quest_id>")
def accept(quest_id: int):
    user = session.get("user")
    if utils.accept_quest(quest_id, user["username"]):
        flash("Acceptしました")
    else:
        flash("操作できません")
    return redirect(url_for("quest_box.detail", quest_id=quest_id))


@bp.route("/complete/<int:quest_id>")
def complete(quest_id: int):
    user = session.get("user")
    quests = utils.load_quests()
    quest = next((q for q in quests if q.get("id") == quest_id), None)
    if not quest:
        flash("該当IDがありません")
        return redirect(url_for("quest_box.index"))
    if user["role"] != "admin" and quest.get("accepted_by") != user["username"]:
        flash("権限がありません")
        return redirect(url_for("quest_box.detail", quest_id=quest_id))
    utils.complete_quest(quest_id)
    flash("完了しました")
    return redirect(url_for("quest_box.detail", quest_id=quest_id))


@bp.route("/delete/<int:quest_id>")
def delete(quest_id: int):
    user = session.get("user")
    if user["role"] != "admin":
        flash("権限がありません")
        return redirect(url_for("quest_box.index"))
    if utils.delete_quest(quest_id):
        flash("削除しました")
    else:
        flash("該当IDがありません")
    return redirect(url_for("quest_box.index"))


@bp.route("/reward/<int:quest_id>", methods=["GET", "POST"])
def reward(quest_id: int):
    user = session.get("user")
    if user["role"] != "admin":
        flash("権限がありません")
        return redirect(url_for("quest_box.detail", quest_id=quest_id))
    quests = utils.load_quests()
    quest = next((q for q in quests if q.get("id") == quest_id), None)
    if not quest:
        flash("該当IDがありません")
        return redirect(url_for("quest_box.index"))
    form = RewardForm(reward=quest.get("reward"))
    if form.validate_on_submit():
        utils.set_reward(quest_id, form.reward.data or "")
        flash("保存しました")
        return redirect(url_for("quest_box.detail", quest_id=quest_id))
    return render_template("quest_box/order_create_form.html", form=form, user=user)
