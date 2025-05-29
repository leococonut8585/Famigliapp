"""Routes for Seminario blueprint."""

from flask import render_template, session, redirect, url_for, flash, request
from datetime import date # For feedback deadline check

from . import bp
# LessonFeedbackForm is no longer used for a dedicated page/route
from .forms import LessonScheduleForm
from . import utils


@bp.before_request
def require_login():
    if "user" not in session:
        # Pass the original URL to the login page for redirection after login
        return redirect(url_for("auth.login", next=request.url))


@bp.route("/")
def index():
    user = session.get("user")
    entries = utils.get_active_seminars()
    # Sort by lesson_date (start date), newest first. Ensure robust sorting.
    entries.sort(key=lambda e: e.get("lesson_date") or "", reverse=True)
    return render_template("seminario_list.html", entries=entries, user=user)


@bp.route("/schedule", methods=["GET", "POST"])
def schedule():
    user = session.get("user")
    form = LessonScheduleForm()
    if form.validate_on_submit():
        # Note: form.seminar_end_date and form.calendar_event_type
        # are expected to be added to LessonScheduleForm in a later task.
        # The order of arguments matches the definition in utils.add_schedule:
        # (author, lesson_date, title, calendar_event_type, seminar_end_date)
        utils.add_schedule(
            author=user["username"],
            lesson_date=form.date.data,  # This is the seminar start date
            title=form.title.data,
            calendar_event_type=form.calendar_event_type.data,
            seminar_end_date=form.seminar_end_date.data,
        )
        flash("新しいセミナーを登録しました。", "success")
        return redirect(url_for(".index"))
    return render_template("seminario_schedule_form.html", form=form, user=user)


# The old feedback(entry_id) route has been removed.
# Its functionality is replaced by feedback_submission_page and submit_feedback_for_seminar.


@bp.route("/confirm")
def confirm_list():
    user = session.get("user")
    seminars = utils.get_kouza_seminars()
    # Sort by lesson_date (start date), newest first
    seminars.sort(key=lambda e: e.get("lesson_date") or "", reverse=True)
    return render_template("seminario_confirm_list.html", seminars=seminars, user=user)


@bp.route("/feedback_submission")
def feedback_submission_page():
    user = session.get("user")
    # Fetches seminars and marks if user has submitted feedback for each
    seminars_for_feedback = utils.get_seminars_for_feedback_page(user["username"])
    # Sort by feedback_deadline, newest first
    seminars_for_feedback.sort(key=lambda e: e.get("feedback_deadline") or "", reverse=True)
    return render_template(
        "seminario_feedback_submission.html",
        seminars_for_feedback=seminars_for_feedback,
        user=user,  # Pass user object for current_user.username in template
    )


@bp.route("/submit_feedback/<int:entry_id>", methods=["POST"])
def submit_feedback_for_seminar(entry_id: int):
    user = session.get("user")
    body = request.form.get("body", "").strip()

    seminar = utils.get_seminar_by_id(entry_id)
    if not seminar:
        flash("指定されたセミナーが見つかりません。", "danger")
        return redirect(url_for(".feedback_submission_page"))

    # Check if seminar is a 'kouza' type, as feedback is for 'kouza'
    if seminar.get("calendar_event_type") != "kouza":
        flash("この種類のセミナーには感想を投稿できません。", "warning")
        return redirect(url_for(".feedback_submission_page"))
        
    # Check if seminar is active
    if seminar.get("status") != "active":
        flash("このセミナーは現在アクティブではないため、感想を投稿できません。", "warning")
        return redirect(url_for(".feedback_submission_page"))

    # Check if feedback deadline has passed
    today = date.today()
    feedback_deadline_str = seminar.get("feedback_deadline")
    if feedback_deadline_str:
        try:
            feedback_deadline_date = date.fromisoformat(feedback_deadline_str)
            if today > feedback_deadline_date:
                flash("このセミナーの感想投稿期限は過ぎています。", "warning")
                return redirect(url_for(".feedback_submission_page"))
        except ValueError:
            flash("セミナーの締切日フォーマットが無効です。", "danger") # Should not happen with good data
            return redirect(url_for(".feedback_submission_page"))
            
    if len(body) < 300:
        flash("感想は300文字以上で入力してください。もう少し詳しく教えていただけますか？", "warning")
        return redirect(url_for(".feedback_submission_page"))
    
    # Check if user has already submitted feedback (server-side check)
    if user["username"] in seminar.get("feedback_submissions", {}):
        flash("既にこのセミナーに関する感想を投稿済みです。", "info")
        return redirect(url_for(".feedback_submission_page"))

    if utils.add_feedback(entry_id, user["username"], body):
        flash("感想を投稿しました。ありがとうございます！", "success")
    else:
        # This typically means the seminar ID was not found in utils.add_feedback,
        # but we already checked for seminar existence. Could be a save error.
        flash("感想の投稿中にエラーが発生しました。", "danger")
    return redirect(url_for(".feedback_submission_page"))


@bp.route("/completed")
def completed_list():
    user = session.get("user")
    completed_seminars = utils.get_completed_seminars()
    # Sort by seminar_end_date, newest first
    completed_seminars.sort(key=lambda e: e.get("seminar_end_date") or "", reverse=True)
    return render_template(
        "seminario_completed_list.html",
        completed_seminars=completed_seminars,
        user=user,
    )


@bp.route("/complete_seminar/<int:entry_id>", methods=["POST"])
def mark_seminar_completed(entry_id: int):
    user = session.get("user")
    if user.get("role") != "admin":
        flash("管理者権限が必要です。", "danger")
        return redirect(url_for(".index"))

    seminar = utils.get_seminar_by_id(entry_id)
    if not seminar:
        flash("指定されたセミナーが見つかりません。", "danger")
        # confirm_list is a good place for admins to come from/return to for this action
        return redirect(url_for(".confirm_list"))

    if seminar.get("status") == "completed":
        flash(f"セミナー「{seminar.get('title', '')}」は既に完了としてマークされています。", "info")
    elif utils.complete_seminar(entry_id):
        flash(f"セミナー「{seminar.get('title', '')}」を完了にしました。", "success")
    else:
        flash("セミナーの完了処理中にエラーが発生しました。", "danger")
    
    return redirect(url_for(".confirm_list"))
