"""Routes for Decima (formerly Principessina) blueprint."""

import os
from flask import (
    render_template,
    session,
    redirect,
    url_for,
    flash,
    request,
    send_from_directory, 
    current_app 
)
from app.utils import save_uploaded_file 
from datetime import datetime, date

from . import bp
from .forms import ReportForm, VideoUploadForm, PhotoUploadForm, CreateCustomFolderForm # Added PhotoUploadForm
from . import utils

# Base directory for all Principessina uploads within static/uploads/
PRINCIPESSINA_UPLOAD_BASE_DIR_REL_TO_STATIC_UPLOADS = "principessina"
# Specific directories for media types relative to PRINCIPESSINA_UPLOAD_BASE_DIR
VIDEO_DIR_REL_TO_PRINCIPESSINA_UPLOADS = "videos"
PHOTO_DIR_REL_TO_PRINCIPESSINA_UPLOADS = "photos" # New constant for photos


@bp.before_request
def require_login():
    if "user" not in session:
        return redirect(url_for("auth.login", next=request.url))

# --- Helper Function ---
def get_principessina_base_upload_path_abs():
    """Returns absolute path to static/uploads/principessina"""
    return os.path.join(current_app.static_folder, "uploads", PRINCIPESSINA_UPLOAD_BASE_DIR_REL_TO_STATIC_UPLOADS)

# --- Text Report Routes (Yura, Mangiato) ---
@bp.route("/")
def index():
    user = session.get("user")
    return render_template("principessina_feed.html", user=user)

@bp.route('/yura', methods=['GET', 'POST'])
def yura_report():
    user = session.get("user")
    form = ReportForm()
    if form.validate_on_submit():
        text = form.text_content.data
        if len(text) < 200:
            flash("短すぎるね、200文字以上になるようにもう少し集中したほうが良い", "warning")
        else:
            utils.add_report(author=user['username'], report_type="yura", text_content=text)
            flash("「今日のユラちゃん」を報告しました。", "success")
            return redirect(url_for('.yura_report'))
    today_yura_reports = [
        r for r in utils.get_active_reports(report_type="yura") 
        if datetime.fromisoformat(r['timestamp']).date() == date.today()
    ]
    today_yura_reports.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return render_template("decima_yura_report.html", form=form, reports=today_yura_reports, user=user)

@bp.route('/mangiato', methods=['GET', 'POST'])
def mangiato_report():
    user = session.get("user")
    form = ReportForm()
    if form.validate_on_submit():
        text = form.text_content.data
        utils.add_report(author=user['username'], report_type="mangiato", text_content=text)
        flash("「食べたもの」を報告しました。", "success")
        return redirect(url_for('.mangiato_report'))
    today_mangiato_reports = [
        r for r in utils.get_active_reports(report_type="mangiato")
        if datetime.fromisoformat(r['timestamp']).date() == date.today()
    ]
    today_mangiato_reports.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return render_template("decima_mangiato_report.html", form=form, reports=today_mangiato_reports, user=user)

@bp.route("/delete_report/<int:report_id>")
def delete_report(report_id: int):
    user = session.get("user")
    if user.get("role") != "admin":
        flash("権限がありません。", "danger")
        return redirect(url_for(".index"))
    all_reports = utils.load_posts() 
    found_report = next((r for r in all_reports if r.get("id") == report_id), None)
    report_type_for_redirect = None
    if found_report: report_type_for_redirect = found_report.get("report_type")
    if utils.delete_post(report_id): flash("報告を削除しました。", "success")
    else: flash("該当IDの報告が見つかりません。", "warning")
    if report_type_for_redirect == "yura": return redirect(url_for(".yura_report"))
    if report_type_for_redirect == "mangiato": return redirect(url_for(".mangiato_report"))
    return redirect(url_for(".index"))

# --- Media Feature Routes (Video, Photo) ---

@bp.route('/video', methods=['GET', 'POST'])
def video_page():
    user = session.get("user")
    video_form = VideoUploadForm()
    folder_form = CreateCustomFolderForm()
    current_folder_name = request.args.get('current_folder')
    
    # Absolute path to static/uploads/principessina/videos
    media_type_base_path_abs = os.path.join(get_principessina_base_upload_path_abs(), VIDEO_DIR_REL_TO_PRINCIPESSINA_UPLOADS)
    os.makedirs(media_type_base_path_abs, exist_ok=True)

    if request.method == 'POST':
        if request.form.get('form_type') == 'upload_video' and video_form.validate_on_submit():
            file = video_form.video_file.data
            title = video_form.title.data
            db_custom_folder_name = current_folder_name
            
            if current_folder_name:
                # Uploading to a specific custom folder
                target_dir_for_upload_abs = os.path.join(media_type_base_path_abs, "custom", current_folder_name)
                # server_path_prefix_for_db is like "principessina/videos/custom/myfolder"
                server_path_prefix_for_db = os.path.join(PRINCIPESSINA_UPLOAD_BASE_DIR_REL_TO_STATIC_UPLOADS, VIDEO_DIR_REL_TO_PRINCIPESSINA_UPLOADS, "custom", current_folder_name)
            else:
                # Uploading to year/month/week folder
                now = datetime.now()
                year, month, week = now.year, now.month, now.isocalendar()[1]
                # year_week_path_part is 'videos/YYYY/MM/WW' (relative to 'static/uploads/principessina')
                year_week_path_part = utils.ensure_media_folder_structure(get_principessina_base_upload_path_abs(), "videos", year, month, week)
                target_dir_for_upload_abs = os.path.join(get_principessina_base_upload_path_abs(), year_week_path_part)
                # server_path_prefix_for_db is like "principessina/videos/YYYY/MM/WW"
                server_path_prefix_for_db = os.path.join(PRINCIPESSINA_UPLOAD_BASE_DIR_REL_TO_STATIC_UPLOADS, year_week_path_part)
                db_custom_folder_name = None

            os.makedirs(target_dir_for_upload_abs, exist_ok=True)
            try:
                saved_filename = save_uploaded_file(file, target_dir_for_upload_abs, utils.ALLOWED_VIDEO_EXTS, utils.MAX_MEDIA_SIZE)
                server_filepath_for_db = os.path.join(server_path_prefix_for_db, saved_filename)
                utils.add_media_entry(
                    uploader_username=user['username'], media_type="video",
                    original_filename=file.filename, server_filepath=server_filepath_for_db,
                    title=title, custom_folder_name=db_custom_folder_name)
                flash("動画をアップロードしました。", "success")
            except ValueError as e: flash(str(e), "danger")
            return redirect(url_for('.video_page', current_folder=current_folder_name))

        elif request.form.get('form_type') == 'create_folder' and folder_form.validate_on_submit():
            new_folder_name = folder_form.folder_name.data
            success, message = utils.create_custom_media_folder(media_type_base_path_abs, new_folder_name)
            flash(message, "success" if success else "danger")
            return redirect(url_for('.video_page', current_folder=new_folder_name if success else current_folder_name))

    custom_folders = utils.get_custom_folders(media_type_base_path_abs)
    media_entries = utils.get_media_entries(media_type="video", custom_folder_name=current_folder_name)
    media_entries.sort(key=lambda x: x.get("upload_timestamp", ""), reverse=True)
    current_folder_display_name = current_folder_name if current_folder_name else "年月フォルダ"

    return render_template("decima_video_page.html", 
        video_form=video_form, folder_form=folder_form, video_entries=media_entries, 
        custom_video_folders=custom_folders, current_folder_name=current_folder_name,
        current_folder_display_name=current_folder_display_name, user=user)

@bp.route('/photo', methods=['GET', 'POST'])
def photo_page():
    user = session.get("user")
    photo_form = PhotoUploadForm()
    folder_form = CreateCustomFolderForm()
    current_folder_name = request.args.get('current_folder')

    # Absolute path to static/uploads/principessina/photos
    media_type_base_path_abs = os.path.join(get_principessina_base_upload_path_abs(), PHOTO_DIR_REL_TO_PRINCIPESSINA_UPLOADS)
    os.makedirs(media_type_base_path_abs, exist_ok=True) 

    if request.method == 'POST':
        if request.form.get('form_type') == 'upload_photo' and photo_form.validate_on_submit():
            file = photo_form.photo_file.data
            title = photo_form.title.data
            db_custom_folder_name = current_folder_name

            if current_folder_name:
                target_dir_for_upload_abs = os.path.join(media_type_base_path_abs, "custom", current_folder_name)
                server_path_prefix_for_db = os.path.join(PRINCIPESSINA_UPLOAD_BASE_DIR_REL_TO_STATIC_UPLOADS, PHOTO_DIR_REL_TO_PRINCIPESSINA_UPLOADS, "custom", current_folder_name)
            else:
                now = datetime.now()
                year, month, week = now.year, now.month, now.isocalendar()[1]
                # year_week_path_part is 'photos/YYYY/MM/WW' (relative to 'static/uploads/principessina')
                year_week_path_part = utils.ensure_media_folder_structure(get_principessina_base_upload_path_abs(), "photos", year, month, week)
                target_dir_for_upload_abs = os.path.join(get_principessina_base_upload_path_abs(), year_week_path_part)
                server_path_prefix_for_db = os.path.join(PRINCIPESSINA_UPLOAD_BASE_DIR_REL_TO_STATIC_UPLOADS, year_week_path_part)
                db_custom_folder_name = None
            
            os.makedirs(target_dir_for_upload_abs, exist_ok=True)
            try:
                saved_filename = save_uploaded_file(file, target_dir_for_upload_abs, utils.ALLOWED_PHOTO_EXTS, utils.MAX_MEDIA_SIZE)
                server_filepath_for_db = os.path.join(server_path_prefix_for_db, saved_filename)
                utils.add_media_entry(
                    uploader_username=user['username'], media_type="photo",
                    original_filename=file.filename, server_filepath=server_filepath_for_db,
                    title=title, custom_folder_name=db_custom_folder_name)
                flash("写真をアップロードしました。", "success")
            except ValueError as e: flash(str(e), "danger")
            return redirect(url_for('.photo_page', current_folder=current_folder_name))

        elif request.form.get('form_type') == 'create_folder' and folder_form.validate_on_submit():
            new_folder_name = folder_form.folder_name.data
            success, message = utils.create_custom_media_folder(media_type_base_path_abs, new_folder_name)
            flash(message, "success" if success else "danger")
            return redirect(url_for('.photo_page', current_folder=new_folder_name if success else current_folder_name))

    custom_folders = utils.get_custom_folders(media_type_base_path_abs)
    media_entries = utils.get_media_entries(media_type="photo", custom_folder_name=current_folder_name)
    media_entries.sort(key=lambda x: x.get("upload_timestamp", ""), reverse=True)
    current_folder_display_name = current_folder_name if current_folder_name else "年月フォルダ"

    return render_template("decima_photo_page.html", 
        photo_form=photo_form, folder_form=folder_form, photo_entries=media_entries, 
        custom_photo_folders=custom_folders, current_folder_name=current_folder_name,
        current_folder_display_name=current_folder_display_name, user=user)

# --- Common Media Routes ---
@bp.route('/download_media/<path:filepath_in_json>')
def download_media_file(filepath_in_json: str):
    # filepath_in_json is relative to 'static/uploads/'
    directory = os.path.join(current_app.static_folder, 'uploads')
    return send_from_directory(directory, filepath_in_json, as_attachment=True)

@bp.route('/delete_media/<int:media_id>', methods=['POST'])
def delete_media(media_id: int):
    user = session.get("user")
    if user.get("role") != "admin":
        flash("権限がありません。", "danger")
        return redirect(request.referrer or url_for('.index')) # Redirect to referrer or Decima index

    # base_static_uploads_path for delete_media_entry is 'static/uploads'
    base_static_uploads_abs = os.path.join(current_app.static_folder, 'uploads')
    
    # Determine media type for redirect by fetching the entry first
    media_entry = utils.get_media_entries() # Get all and find
    entry_to_delete = next((e for e in media_entry if e.get("id") == media_id), None)
    redirect_url = url_for('.index') # Default redirect
    if entry_to_delete:
        if entry_to_delete.get('media_type') == 'video':
            redirect_url = url_for('.video_page', current_folder=entry_to_delete.get('custom_folder_name'))
        elif entry_to_delete.get('media_type') == 'photo':
            redirect_url = url_for('.photo_page', current_folder=entry_to_delete.get('custom_folder_name'))
            
    if utils.delete_media_entry(media_id, base_static_uploads_abs):
        flash("メディアファイルを削除しました。", "success")
    else:
        flash("メディアファイルの削除に失敗しました。", "danger")
    return redirect(request.referrer or redirect_url)
