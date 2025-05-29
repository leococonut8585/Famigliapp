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
from .forms import (
    ReportForm, VideoUploadForm, PhotoUploadForm, 
    CreateCustomFolderForm, CopyMediaToCustomFolderForm # Added CopyMediaToCustomFolderForm
)
from . import utils

PRINCIPESSINA_UPLOAD_BASE_DIR_REL_TO_STATIC_UPLOADS = "principessina"
VIDEO_DIR_REL_TO_PRINCIPESSINA_UPLOADS = "videos"
PHOTO_DIR_REL_TO_PRINCIPESSINA_UPLOADS = "photos"


@bp.before_request
def require_login():
    if "user" not in session:
        return redirect(url_for("auth.login", next=request.url))

def get_principessina_base_upload_path_abs():
    return os.path.join(current_app.static_folder, "uploads", PRINCIPESSINA_UPLOAD_BASE_DIR_REL_TO_STATIC_UPLOADS)

@bp.route("/")
def index():
    user = session.get("user")
    return render_template("principessina_feed.html", user=user)

# --- Text Report Routes ---
@bp.route('/yura', methods=['GET', 'POST'])
def yura_report():
    user = session.get("user")
    form = ReportForm()
    if form.validate_on_submit():
        text = form.text_content.data
        if len(text) < 200: flash("短すぎるね、200文字以上になるようにもう少し集中したほうが良い", "warning")
        else:
            utils.add_report(author=user['username'], report_type="yura", text_content=text)
            flash("「今日のユラちゃん」を報告しました。", "success")
            return redirect(url_for('.yura_report'))
    today_yura_reports = [r for r in utils.get_active_reports(report_type="yura") if datetime.fromisoformat(r['timestamp']).date() == date.today()]
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
    today_mangiato_reports = [r for r in utils.get_active_reports(report_type="mangiato") if datetime.fromisoformat(r['timestamp']).date() == date.today()]
    today_mangiato_reports.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return render_template("decima_mangiato_report.html", form=form, reports=today_mangiato_reports, user=user)

@bp.route("/delete_report/<int:report_id>")
def delete_report(report_id: int):
    user = session.get("user")
    if user.get("role") != "admin":
        flash("権限がありません。", "danger"); return redirect(url_for(".index"))
    all_reports = utils.load_posts() 
    found_report = next((r for r in all_reports if r.get("id") == report_id), None)
    rt = found_report.get("report_type") if found_report else None
    if utils.delete_post(report_id): flash("報告を削除しました。", "success")
    else: flash("該当IDの報告が見つかりません。", "warning")
    if rt == "yura": return redirect(url_for(".yura_report"))
    if rt == "mangiato": return redirect(url_for(".mangiato_report"))
    return redirect(url_for(".index"))

# --- Media Feature Routes ---
@bp.route('/video', methods=['GET', 'POST'])
def video_page():
    user = session.get("user")
    video_form = VideoUploadForm()
    folder_form = CreateCustomFolderForm()
    copy_form = CopyMediaToCustomFolderForm() # New form
    current_folder_name = request.args.get('current_folder')
    
    media_type_base_path_abs = os.path.join(get_principessina_base_upload_path_abs(), VIDEO_DIR_REL_TO_PRINCIPESSINA_UPLOADS)
    os.makedirs(media_type_base_path_abs, exist_ok=True)

    all_custom_folders = utils.get_custom_folders(media_type_base_path_abs)
    copy_form.target_custom_folder.choices = [(folder, folder) for folder in all_custom_folders]

    if request.method == 'POST':
        if request.form.get('form_type') == 'upload_video' and video_form.validate_on_submit():
            file = video_form.video_file.data; title = video_form.title.data
            db_custom_folder_name = current_folder_name
            if current_folder_name:
                target_dir_for_upload_abs = os.path.join(media_type_base_path_abs, "custom", current_folder_name)
                server_path_prefix_for_db = os.path.join(PRINCIPESSINA_UPLOAD_BASE_DIR_REL_TO_STATIC_UPLOADS, VIDEO_DIR_REL_TO_PRINCIPESSINA_UPLOADS, "custom", current_folder_name)
            else:
                now = datetime.now(); year, month, week = now.year, now.month, now.isocalendar()[1]
                year_week_path_part = utils.ensure_media_folder_structure(get_principessina_base_upload_path_abs(), "videos", year, month, week)
                target_dir_for_upload_abs = os.path.join(get_principessina_base_upload_path_abs(), year_week_path_part)
                server_path_prefix_for_db = os.path.join(PRINCIPESSINA_UPLOAD_BASE_DIR_REL_TO_STATIC_UPLOADS, year_week_path_part)
                db_custom_folder_name = None
            os.makedirs(target_dir_for_upload_abs, exist_ok=True)
            try:
                saved_filename = save_uploaded_file(file, target_dir_for_upload_abs, utils.ALLOWED_VIDEO_EXTS, utils.MAX_MEDIA_SIZE)
                server_filepath_for_db = os.path.join(server_path_prefix_for_db, saved_filename)
                utils.add_media_entry(user['username'], "video", file.filename, server_filepath_for_db, title, db_custom_folder_name)
                flash("動画をアップロードしました。", "success")
            except ValueError as e: flash(str(e), "danger")
            return redirect(url_for('.video_page', current_folder=current_folder_name))
        elif request.form.get('form_type') == 'create_folder' and folder_form.validate_on_submit():
            new_folder_name = folder_form.folder_name.data
            success, message = utils.create_custom_media_folder(media_type_base_path_abs, new_folder_name)
            flash(message, "success" if success else "danger")
            return redirect(url_for('.video_page', current_folder=new_folder_name if success else current_folder_name))

    media_entries = utils.get_media_entries(media_type="video", custom_folder_name=current_folder_name)
    media_entries.sort(key=lambda x: x.get("upload_timestamp", ""), reverse=True)
    current_folder_display_name = current_folder_name if current_folder_name else "年月フォルダ"
    return render_template("decima_video_page.html", 
        video_form=video_form, folder_form=folder_form, copy_form=copy_form, # Added copy_form
        video_entries=media_entries, custom_video_folders=all_custom_folders, # Renamed for clarity
        all_custom_video_folders=all_custom_folders, # Explicitly for template
        current_folder_name=current_folder_name,
        current_folder_display_name=current_folder_display_name, user=user)

@bp.route('/photo', methods=['GET', 'POST'])
def photo_page():
    user = session.get("user")
    photo_form = PhotoUploadForm()
    folder_form = CreateCustomFolderForm()
    copy_form = CopyMediaToCustomFolderForm() # New form
    current_folder_name = request.args.get('current_folder')

    media_type_base_path_abs = os.path.join(get_principessina_base_upload_path_abs(), PHOTO_DIR_REL_TO_PRINCIPESSINA_UPLOADS)
    os.makedirs(media_type_base_path_abs, exist_ok=True) 

    all_custom_folders = utils.get_custom_folders(media_type_base_path_abs)
    copy_form.target_custom_folder.choices = [(folder, folder) for folder in all_custom_folders]

    if request.method == 'POST':
        if request.form.get('form_type') == 'upload_photo' and photo_form.validate_on_submit():
            file = photo_form.photo_file.data; title = photo_form.title.data
            db_custom_folder_name = current_folder_name
            if current_folder_name:
                target_dir_for_upload_abs = os.path.join(media_type_base_path_abs, "custom", current_folder_name)
                server_path_prefix_for_db = os.path.join(PRINCIPESSINA_UPLOAD_BASE_DIR_REL_TO_STATIC_UPLOADS, PHOTO_DIR_REL_TO_PRINCIPESSINA_UPLOADS, "custom", current_folder_name)
            else:
                now = datetime.now(); year, month, week = now.year, now.month, now.isocalendar()[1]
                year_week_path_part = utils.ensure_media_folder_structure(get_principessina_base_upload_path_abs(), "photos", year, month, week)
                target_dir_for_upload_abs = os.path.join(get_principessina_base_upload_path_abs(), year_week_path_part)
                server_path_prefix_for_db = os.path.join(PRINCIPESSINA_UPLOAD_BASE_DIR_REL_TO_STATIC_UPLOADS, year_week_path_part)
                db_custom_folder_name = None
            os.makedirs(target_dir_for_upload_abs, exist_ok=True)
            try:
                saved_filename = save_uploaded_file(file, target_dir_for_upload_abs, utils.ALLOWED_PHOTO_EXTS, utils.MAX_MEDIA_SIZE)
                server_filepath_for_db = os.path.join(server_path_prefix_for_db, saved_filename)
                utils.add_media_entry(user['username'], "photo", file.filename, server_filepath_for_db, title, db_custom_folder_name)
                flash("写真をアップロードしました。", "success")
            except ValueError as e: flash(str(e), "danger")
            return redirect(url_for('.photo_page', current_folder=current_folder_name))
        elif request.form.get('form_type') == 'create_folder' and folder_form.validate_on_submit():
            new_folder_name = folder_form.folder_name.data
            success, message = utils.create_custom_media_folder(media_type_base_path_abs, new_folder_name)
            flash(message, "success" if success else "danger")
            return redirect(url_for('.photo_page', current_folder=new_folder_name if success else current_folder_name))

    media_entries = utils.get_media_entries(media_type="photo", custom_folder_name=current_folder_name)
    media_entries.sort(key=lambda x: x.get("upload_timestamp", ""), reverse=True)
    current_folder_display_name = current_folder_name if current_folder_name else "年月フォルダ"
    return render_template("decima_photo_page.html", 
        photo_form=photo_form, folder_form=folder_form, copy_form=copy_form, # Added copy_form
        photo_entries=media_entries, custom_photo_folders=all_custom_folders, # Renamed for clarity
        all_custom_photo_folders=all_custom_folders, # Explicitly for template
        current_folder_name=current_folder_name,
        current_folder_display_name=current_folder_display_name, user=user)

# --- Common Media Routes ---
@bp.route('/media/<int:media_id>/copy_to_folder', methods=['POST'])
def copy_media_to_folder(media_id: int):
    user = session.get("user") # Ensure user is logged in
    form = CopyMediaToCustomFolderForm(request.form) # Pass request.form
    media_type = request.form.get('media_type') # "video" or "photo"
    source_folder = request.form.get('source_folder') # To redirect back

    # Determine base path for the media type to get custom folder choices
    if media_type == "video":
        media_type_base_path_abs = os.path.join(get_principessina_base_upload_path_abs(), VIDEO_DIR_REL_TO_PRINCIPESSINA_UPLOADS)
    elif media_type == "photo":
        media_type_base_path_abs = os.path.join(get_principessina_base_upload_path_abs(), PHOTO_DIR_REL_TO_PRINCIPESSINA_UPLOADS)
    else:
        flash("無効なメディアタイプです。", "danger"); return redirect(url_for(".index"))
    
    all_custom_folders = utils.get_custom_folders(media_type_base_path_abs)
    form.target_custom_folder.choices = [(folder, folder) for folder in all_custom_folders]

    if form.validate_on_submit():
        target_folder = form.target_custom_folder.data
        success = utils.add_media_reference_to_custom_folder(media_id, target_folder)
        if success: flash(f"メディアをカスタムフォルダ「{target_folder}」にコピー（参照追加）しました。", "success")
        else: flash("メディアのコピー（参照追加）に失敗しました。既に参照されているか、プライマリフォルダ、またはIDが見つかりません。", "warning")
    else:
        for field, errors in form.errors.items():
            flash(f"エラー ({getattr(form, field).label.text}): {', '.join(errors)}", "danger")

    if media_type == "video": return redirect(url_for('.video_page', current_folder=source_folder if source_folder else None))
    if media_type == "photo": return redirect(url_for('.photo_page', current_folder=source_folder if source_folder else None))
    return redirect(url_for(".index"))

@bp.route('/media/<int:media_id>/remove_reference', methods=['POST'])
def remove_media_reference(media_id: int):
    user = session.get("user") # Ensure user is logged in
    folder_to_remove = request.form.get('folder_to_remove')
    media_type = request.form.get('media_type')

    if not folder_to_remove:
        flash("削除対象のフォルダが指定されていません。", "danger")
    else:
        success = utils.remove_media_reference_from_custom_folder(media_id, folder_to_remove)
        if success: flash(f"カスタムフォルダ「{folder_to_remove}」からのメディア参照を削除しました。", "success")
        else: flash("メディア参照の削除に失敗しました。エントリーが見つからない可能性があります。", "warning")
    
    redirect_to_folder = folder_to_remove # Redirect back to the folder from which reference was removed
    if media_type == "video": return redirect(url_for('.video_page', current_folder=redirect_to_folder))
    if media_type == "photo": return redirect(url_for('.photo_page', current_folder=redirect_to_folder))
    return redirect(url_for(".index"))

@bp.route('/download_media/<path:filepath_in_json>')
def download_media_file(filepath_in_json: str):
    directory = os.path.join(current_app.static_folder, 'uploads')
    return send_from_directory(directory, filepath_in_json, as_attachment=True)

@bp.route('/delete_media/<int:media_id>', methods=['POST'])
def delete_media(media_id: int):
    user = session.get("user")
    if user.get("role") != "admin":
        flash("権限がありません。", "danger")
        return redirect(request.referrer or url_for('.index'))
    
    base_static_uploads_abs = os.path.join(current_app.static_folder, 'uploads')
    # Store media details before attempting deletion for intelligent redirect
    media_entries_list = utils.load_media_entries() # Use load_media_entries to get raw data
    entry_to_delete = next((e for e in media_entries_list if e.get("id") == media_id), None)
    
    redirect_url = url_for('.index') # Default redirect
    if entry_to_delete:
        media_type = entry_to_delete.get('media_type')
        # Use request.form.get to get source_folder from the delete form in template
        # This was added to the template in previous steps
        source_folder = request.form.get('source_folder') 
        if media_type == 'video':
            redirect_url = url_for('.video_page', current_folder=source_folder if source_folder else None)
        elif media_type == 'photo':
            redirect_url = url_for('.photo_page', current_folder=source_folder if source_folder else None)
            
    if utils.delete_media_entry(media_id, base_static_uploads_abs):
        flash("メディアファイルを削除しました。", "success")
    else:
        flash("メディアファイルの削除に失敗しました。", "danger")
    
    # Try to redirect to request.referrer if available and reasonable, else to calculated redirect_url
    # However, request.referrer can be unreliable or not what you want after a POST.
    # The calculated redirect_url is safer.
    return redirect(redirect_url)
