"""Routes for Monsignore blueprint."""

import os
from flask import render_template, session, redirect, url_for, flash, request, send_from_directory
from app.utils import save_uploaded_file, send_email # Added send_email
import config
from datetime import datetime, date

from . import bp
from .forms import AddKadaiForm
from . import utils

UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "uploads", "monsignore_kadai"))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@bp.before_request
def require_login():
    if "user" not in session:
        return redirect(url_for("auth.login", next=request.url))


@bp.route("/")
def index():
    user = session.get("user")
    return render_template("monsignore_list.html", user=user)

@bp.route('/kadai')
def kadai_list():
    user = session.get("user")
    kadai_entries = utils.get_active_kadai_entries()
    kadai_entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return render_template("monsignore_kadai_list.html", kadai_entries=kadai_entries, user=user)

@bp.route('/archive')
def archive_list():
    user = session.get("user")
    archived_kadai_entries = utils.get_archived_kadai_entries()
    archived_kadai_entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return render_template("monsignore_archive_list.html", archived_kadai_entries=archived_kadai_entries, user=user)

@bp.route('/kadai_download/<path:filename>')
def download_kadai_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


@bp.route('/kadai_feedback_page')
def kadai_feedback_page():
    user = session.get("user")
    active_kadai = utils.get_active_kadai_entries()

    for kadai_entry in active_kadai:
        user_feedback = kadai_entry.get("feedback_submissions", {}).get(user["username"])
        if user_feedback:
            kadai_entry['user_has_submitted'] = True
            kadai_entry['user_feedback_text'] = user_feedback.get('text')
        else:
            kadai_entry['user_has_submitted'] = False
            kadai_entry['user_feedback_text'] = None

    active_kadai.sort(key=lambda x: x.get("feedback_deadline") or x.get("timestamp",""), reverse=True)

    return render_template(
        "monsignore_feedback_page.html",
        kadai_entries_for_feedback=active_kadai,
        user=user
    )

@bp.route('/kadai_feedback_submit/<int:kadai_id>', methods=['POST'])
def submit_kadai_feedback(kadai_id: int):
    user = session.get("user")
    feedback_text = request.form.get("feedback_text", "").strip()

    kadai_entry = utils.get_kadai_entry_by_id(kadai_id)

    if not kadai_entry:
        flash("指定された「言葉」が見つかりません。", "danger")
        return redirect(url_for('.kadai_feedback_page'))

    if len(feedback_text) < 300:
        flash("短すぎるね、300文字以上になるようにもう少し集中したほうが良い", "warning")
        return redirect(url_for('.kadai_feedback_page'))

    if user["username"] in kadai_entry.get("feedback_submissions", {}):
        flash("既にこの「言葉」に関する感想を投稿済みです。", "info")
        return redirect(url_for('.kadai_feedback_page'))

    if utils.add_feedback_to_kadai(kadai_id, user["username"], feedback_text):
        flash("感想を投稿しました。ありがとうございます！", "success")
    else:
        flash("感想の投稿中にエラーが発生しました。エントリーが存在しないか、アクティブでない可能性があります。", "danger")
    return redirect(url_for('.kadai_feedback_page'))


@bp.route("/add", methods=["GET", "POST"])
def add():
    user = session.get("user")
    form = AddKadaiForm()
    if form.validate_on_submit():
        filename = None
        file_type = None
        original_filename = None

        if form.attachment.data and form.attachment.data.filename:
            original_filename = form.attachment.data.filename
            try:
                filename = save_uploaded_file(
                    form.attachment.data,
                    UPLOAD_FOLDER,
                    utils.KADAI_ALLOWED_EXTS,
                    utils.MAX_KADAI_FILE_SIZE,
                )
                ext = os.path.splitext(original_filename)[1].lower()
                if ext in {".png", ".jpg", ".jpeg", ".gif"}:
                    file_type = "image"
                elif ext in {".mp4", ".mov", ".avi", ".wmv", ".mkv"}:
                    file_type = "video"
                else:
                    file_type = "other"
            except ValueError as e:
                flash(str(e), "danger")
                return render_template(
                    "monsignore_kadai_form.html",
                    form=form,
                    user=user,
                    allowed_exts_str=", ".join(utils.KADAI_ALLOWED_EXTS),
                    max_size_mb=int(utils.MAX_KADAI_FILE_SIZE / (1024*1024))
                )

        new_kadai_id = utils.add_kadai_entry(
            author=user["username"],
            title=form.title.data,
            text_body=form.text_body.data,
            filename=filename,
            file_type=file_type,
            original_filename=original_filename
        )

        # Immediate Notification Logic
        if new_kadai_id:
            new_kadai = utils.get_kadai_entry_by_id(new_kadai_id)
            if new_kadai:
                kadai_title = new_kadai.get("title", "N/A")
                kadai_author = new_kadai.get("author", "N/A")
                # Ensure feedback_deadline is a string suitable for display
                feedback_deadline_str = new_kadai.get("feedback_deadline", "N/A")
                if 'T' in feedback_deadline_str: # Simple check if it's likely ISO format
                    feedback_deadline_display = feedback_deadline_str.split('T')[0]
                else:
                    feedback_deadline_display = feedback_deadline_str

                kadai_url = url_for('monsignore.kadai_list', _external=True) # Or specific kadai view if exists

                if hasattr(config, "USERS") and isinstance(config.USERS, dict):
                    for username, user_data in config.USERS.items():
                        if isinstance(user_data, dict) and \
                           user_data.get("role") != "admin" and \
                           user_data.get("email"):

                            email_subject = f"新しい「言葉」が追加されました: {kadai_title}"
                            email_body = (
                                f"新しい「言葉」が {kadai_author} さんによって追加されました。\n\n"
                                f"タイトル: {kadai_title}\n"
                                f"締切: {feedback_deadline_display}\n\n"
                                f"確認・感想投稿はこちら: {kadai_url}"
                            )
                            send_email(email_subject, email_body, user_data["email"])

        flash("新しい「言葉」を投稿しました。", "success")
        return redirect(url_for(".kadai_list"))

    return render_template(
        "monsignore_kadai_form.html",
        form=form,
        user=user,
        allowed_exts_str=", ".join(utils.KADAI_ALLOWED_EXTS),
        max_size_mb=int(utils.MAX_KADAI_FILE_SIZE / (1024*1024))
    )


@bp.route("/delete/<int:kadai_id>")
def delete(kadai_id: int):
    user = session.get("user")
    if user.get("role") != "admin":
        flash("権限がありません。", "danger")
        return redirect(url_for(".kadai_list"))

    kadai_entry = utils.get_kadai_entry_by_id(kadai_id)
    if not kadai_entry:
        flash("該当IDの「言葉」エントリーが見つかりません。", "warning")
        return redirect(url_for(".kadai_list"))

    if kadai_entry.get("filename"):
        try:
            file_path = os.path.join(UPLOAD_FOLDER, kadai_entry["filename"])
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            flash(f"エントリーのファイル削除中にエラーが発生しました: {e}", "danger")

    if utils.delete_kadai_entry(kadai_id):
        flash("「言葉」のエントリーを削除しました。", "success")
    else:
        flash("「言葉」エントリーの削除中にエラーが発生しました。", "danger")
    return redirect(url_for(".kadai_list"))
