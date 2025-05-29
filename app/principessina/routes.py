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
from datetime import datetime, date, timedelta # Added timedelta for report submission reporting day logic

from . import bp
from .forms import (
    ReportForm, VideoUploadForm, PhotoUploadForm, 
    CreateCustomFolderForm, CopyMediaToCustomFolderForm,
    CreateCustomReportFolderForm, CopyReportToCustomFolderForm,
    SearchPassatoForm # Ensured SearchPassatoForm is imported
)
from . import utils
# Import calendario utils for shift checking
from app.calendario import utils as calendario_utils


PRINCIPESSINA_UPLOAD_BASE_DIR_REL_TO_STATIC_UPLOADS = "principessina"
VIDEO_DIR_REL_TO_PRINCIPESSINA_UPLOADS = "videos"
PHOTO_DIR_REL_TO_PRINCIPESSINA_UPLOADS = "photos"


@bp.before_request
def require_login():
    if "user" not in session:
        return redirect(url_for("auth.login", next=request.url))

def get_principessina_base_upload_path_abs():
    return os.path.join(current_app.static_folder, "uploads", PRINCIPESSINA_UPLOAD_BASE_DIR_REL_TO_STATIC_UPLOADS)

def determine_reporting_day_for_submission() -> date:
    """Determines the reporting day based on current time (before 5 AM is previous day)."""
    # Shift ends at 4 AM, report due by then. Submissions after 4 AM count for current calendar day.
    # Let's consider submissions before 5 AM to be for the previous calendar day's shift.
    if datetime.now().hour < 5: # Before 5 AM
        return date.today() - timedelta(days=1)
    return date.today()

@bp.route("/")
def index():
    user = session.get("user")
    return render_template("principessina_feed.html", user=user)

# --- Text Report Routes ---
@bp.route('/yura', methods=['GET', 'POST'])
def yura_report():
    user = session.get("user")
    form = ReportForm()

    current_reporting_day = determine_reporting_day_for_submission()
    try:
        shift_users_today = calendario_utils.get_users_on_shift(current_reporting_day)
    except FileNotFoundError: # Handle missing calendario.json gracefully for now
        flash("カレンダーデータが見つかりません。管理者に連絡してください。", "danger")
        shift_users_today = [] # Assume no one is on shift if calendar is missing
        # Potentially redirect or disable form, but for now, allow attempt if user proceeds
        
    if request.method == 'POST':
        if user['username'] not in shift_users_today and user.get("role") != "admin": # Admins can bypass
            flash(f"{current_reporting_day.strftime('%Y-%m-%d')}のシフト担当者ではないため、報告を投稿できません。", "warning")
            return redirect(url_for('.yura_report')) # Or .index

        if form.validate_on_submit():
            text = form.text_content.data
            if len(text) < 200: flash("短すぎるね、200文字以上になるようにもう少し集中したほうが良い", "warning")
            else:
                utils.add_report(author=user['username'], report_type="yura", text_content=text)
                flash("「今日のユラちゃん」を報告しました。", "success")
                return redirect(url_for('.yura_report'))
    
    # GET: Fetch today's "yura" reports (for the current calendar day, not reporting day)
    # Display is for current calendar day's submissions.
    today_display_date = date.today()
    today_yura_reports = [
        r for r in utils.get_active_reports(report_type="yura") 
        if datetime.fromisoformat(r['timestamp']).date() == today_display_date
    ]
    today_yura_reports.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    # Check if current user can post (is on shift for the current reporting day)
    can_post = user['username'] in shift_users_today or user.get("role") == "admin"

    return render_template("decima_yura_report.html", form=form, reports=today_yura_reports, user=user, can_post=can_post, reporting_day=current_reporting_day)

@bp.route('/mangiato', methods=['GET', 'POST'])
def mangiato_report():
    user = session.get("user")
    form = ReportForm()

    current_reporting_day = determine_reporting_day_for_submission()
    try:
        shift_users_today = calendario_utils.get_users_on_shift(current_reporting_day)
    except FileNotFoundError:
        flash("カレンダーデータが見つかりません。管理者に連絡してください。", "danger")
        shift_users_today = []

    if request.method == 'POST':
        if user['username'] not in shift_users_today and user.get("role") != "admin": # Admins can bypass
            flash(f"{current_reporting_day.strftime('%Y-%m-%d')}のシフト担当者ではないため、報告を投稿できません。", "warning")
            return redirect(url_for('.mangiato_report'))

        if form.validate_on_submit():
            text = form.text_content.data
            utils.add_report(author=user['username'], report_type="mangiato", text_content=text)
            flash("「食べたもの」を報告しました。", "success")
            return redirect(url_for('.mangiato_report'))

    today_display_date = date.today()
    today_mangiato_reports = [
        r for r in utils.get_active_reports(report_type="mangiato") 
        if datetime.fromisoformat(r['timestamp']).date() == today_display_date
    ]
    today_mangiato_reports.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    can_post = user['username'] in shift_users_today or user.get("role") == "admin"

    return render_template("decima_mangiato_report.html", form=form, reports=today_mangiato_reports, user=user, can_post=can_post, reporting_day=current_reporting_day)

@bp.route("/delete_report/<int:report_id>")
def delete_report(report_id: int):
    # This route is GET based on template links with confirm dialog
    user = session.get("user")
    if user.get("role") != "admin":
        flash("権限がありません。", "danger"); return redirect(url_for(".index"))
    
    all_reports = utils.load_posts() 
    found_report = next((r for r in all_reports if r.get("id") == report_id), None)
    rt = found_report.get("report_type") if found_report else None
    
    # TODO: Also remove references from custom folders if this report is deleted.
    # This requires iterating all custom report folders and removing this report_id.
    # Or, when displaying, check if referenced reports still exist.
    # For now, just deleting the main entry.

    if utils.delete_post(report_id): flash("報告を削除しました。", "success")
    else: flash("該当IDの報告が見つかりません。", "warning")
    
    # Try to redirect to the specific report page if type is known, else to index or referrer
    # For simplicity, redirect to Passato if referrer is Passato, else to specific type page.
    # This needs careful handling if delete is initiated from Passato page.
    # For now, simple redirect.
    if request.referrer and 'passato' in request.referrer:
         return redirect(url_for('.passato_top', **request.args)) # Preserve query params if any

    if rt == "yura": return redirect(url_for(".yura_report"))
    if rt == "mangiato": return redirect(url_for(".mangiato_report"))
    return redirect(url_for(".index"))

@bp.route('/passato', methods=['GET', 'POST'])
def passato_top():
    user = session.get("user")
    search_form = SearchPassatoForm(request.args)
    create_folder_form = CreateCustomReportFolderForm()
    copy_report_form = CopyReportToCustomFolderForm()
    
    current_folder = request.args.get('current_folder')
    phrase = request.args.get('phrase')
    date_from_str = request.args.get('date_from')
    date_to_str = request.args.get('date_to')

    date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date() if date_from_str else None
    date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date() if date_to_str else None

    # Handle folder creation POST
    if request.method == 'POST' and request.form.get('form_type') == 'create_report_folder':
        create_folder_form = CreateCustomReportFolderForm(request.form) # Repopulate with POST data
        if create_folder_form.validate_on_submit():
            new_folder_name = create_folder_form.folder_name.data
            success, message = utils.create_report_custom_folder(new_folder_name)
            flash(message, "success" if success else "danger")
            # Preserve search query params and current_folder on redirect
            query_params = {k: v for k, v in request.args.items() if k != 'current_folder'} # Keep existing search
            query_params['current_folder'] = new_folder_name if success else current_folder
            return redirect(url_for('.passato_top', **query_params))
        # If validation fails, GET logic below will render the page with errors in create_folder_form

    # Process search form on GET, even if it's empty (to pass form object to template)
    # This is implicitly handled by SearchPassatoForm(request.args)
    # No specific search_form.validate_on_submit() here as it's a GET based search.

    archived_reports = utils.get_archived_reports(
        custom_folder_name=current_folder,
        search_phrase=phrase,
        search_date_from=date_from,
        search_date_to=date_to
    )
    custom_report_folders = utils.get_custom_folders_for_reports()
    copy_report_form.target_custom_folder.choices = [(folder, folder) for folder in custom_report_folders]
    
    return render_template(
        "decima_passato_top.html", 
        reports=archived_reports, 
        user=user,
        custom_report_folders=custom_report_folders,
        current_folder_name=current_folder,
        create_folder_form=create_folder_form, # Pass potentially validated or empty form
        copy_report_form=copy_report_form,
        search_form=search_form 
    )

@bp.route('/report/<int:report_id>/copy_to_folder', methods=['POST'])
def copy_report_to_folder(report_id: int):
    user = session.get("user")
    form = CopyReportToCustomFolderForm(request.form)
    
    # Preserve search and folder context for redirect
    redirect_args = {
        'current_folder': request.form.get('source_folder_for_redirect'),
        'phrase': request.form.get('phrase_for_redirect'),
        'date_from': request.form.get('date_from_for_redirect'),
        'date_to': request.form.get('date_to_for_redirect')
    }
    # Remove None or empty string keys for cleaner URL
    redirect_args = {k: v for k, v in redirect_args.items() if v}


    custom_report_folders = utils.get_custom_folders_for_reports()
    form.target_custom_folder.choices = [(folder, folder) for folder in custom_report_folders]

    if form.validate_on_submit():
        target_folder = form.target_custom_folder.data
        success = utils.add_report_reference_to_custom_folder(report_id, target_folder)
        if success: flash(f"報告をフォルダ「{target_folder}」にコピーしました。", "success")
        else: flash("報告のコピーに失敗しました。", "warning")
    else:
        for field, errors in form.errors.items(): flash(f"エラー ({getattr(form, field).label.text}): {', '.join(errors)}", "danger")
    
    return redirect(url_for('.passato_top', **redirect_args))

@bp.route('/report/<int:report_id>/remove_reference', methods=['POST'])
def remove_report_reference(report_id: int):
    user = session.get("user")
    folder_to_remove = request.form.get('folder_to_remove')
    
    redirect_args = {
        'current_folder': folder_to_remove, # Redirect back to the folder it was removed from
        'phrase': request.form.get('phrase_for_redirect'),
        'date_from': request.form.get('date_from_for_redirect'),
        'date_to': request.form.get('date_to_for_redirect')
    }
    redirect_args = {k: v for k, v in redirect_args.items() if v}

    if not folder_to_remove: flash("削除対象のフォルダが指定されていません。", "danger")
    else:
        success = utils.remove_report_reference_from_custom_folder(report_id, folder_to_remove)
        if success: flash(f"フォルダ「{folder_to_remove}」からの報告参照を削除しました。", "success")
        else: flash("報告参照の削除に失敗しました。", "warning")
    
    return redirect(url_for('.passato_top', **redirect_args))

# --- Media Feature Routes (Unchanged) ---
@bp.route('/video', methods=['GET', 'POST'])
def video_page():
    user = session.get("user")
    video_form = VideoUploadForm(); folder_form = CreateCustomFolderForm()
    copy_form = CopyMediaToCustomFolderForm(); current_folder_name = request.args.get('current_folder')
    media_type_base_path_abs = os.path.join(get_principessina_base_upload_path_abs(), VIDEO_DIR_REL_TO_PRINCIPESSINA_UPLOADS)
    os.makedirs(media_type_base_path_abs, exist_ok=True)
    all_custom_folders = utils.get_custom_folders(media_type_base_path_abs)
    copy_form.target_custom_folder.choices = [(f, f) for f in all_custom_folders]
    if request.method == 'POST':
        if request.form.get('form_type') == 'upload_video' and video_form.validate_on_submit():
            file = video_form.video_file.data; title = video_form.title.data; db_custom_folder_name = current_folder_name
            if current_folder_name:
                target_dir_for_upload_abs = os.path.join(media_type_base_path_abs, "custom", current_folder_name)
                s_p_f_db = os.path.join(PRINCIPESSINA_UPLOAD_BASE_DIR_REL_TO_STATIC_UPLOADS, VIDEO_DIR_REL_TO_PRINCIPESSINA_UPLOADS, "custom", current_folder_name)
            else:
                now = datetime.now(); y, m, w = now.year, now.month, now.isocalendar()[1]
                y_w_p_part = utils.ensure_media_folder_structure(get_principessina_base_upload_path_abs(), "videos", y, m, w)
                target_dir_for_upload_abs = os.path.join(get_principessina_base_upload_path_abs(), y_w_p_part)
                s_p_f_db = os.path.join(PRINCIPESSINA_UPLOAD_BASE_DIR_REL_TO_STATIC_UPLOADS, y_w_p_part); db_custom_folder_name = None
            os.makedirs(target_dir_for_upload_abs, exist_ok=True)
            try:
                s_f = save_uploaded_file(file, target_dir_for_upload_abs, utils.ALLOWED_VIDEO_EXTS, utils.MAX_MEDIA_SIZE)
                s_f_db = os.path.join(s_p_f_db, s_f)
                utils.add_media_entry(user['username'], "video", file.filename, s_f_db, title, db_custom_folder_name)
                flash("動画をアップロードしました。", "success")
            except ValueError as e: flash(str(e), "danger")
            return redirect(url_for('.video_page', current_folder=current_folder_name))
        elif request.form.get('form_type') == 'create_folder' and folder_form.validate_on_submit():
            n_f_n = folder_form.folder_name.data; success, message = utils.create_custom_media_folder(media_type_base_path_abs, n_f_n)
            flash(message, "success" if success else "danger")
            return redirect(url_for('.video_page', current_folder=n_f_n if success else current_folder_name))
    media_entries = utils.get_media_entries(media_type="video", custom_folder_name=current_folder_name)
    media_entries.sort(key=lambda x: x.get("upload_timestamp", ""), reverse=True)
    current_folder_display_name = current_folder_name if current_folder_name else "年月フォルダ"
    return render_template("decima_video_page.html", video_form=video_form, folder_form=folder_form, copy_form=copy_form,
        video_entries=media_entries, custom_video_folders=all_custom_folders, all_custom_video_folders=all_custom_folders, 
        current_folder_name=current_folder_name, current_folder_display_name=current_folder_display_name, user=user)

@bp.route('/photo', methods=['GET', 'POST'])
def photo_page():
    user = session.get("user"); photo_form = PhotoUploadForm(); folder_form = CreateCustomFolderForm()
    copy_form = CopyMediaToCustomFolderForm(); current_folder_name = request.args.get('current_folder')
    media_type_base_path_abs = os.path.join(get_principessina_base_upload_path_abs(), PHOTO_DIR_REL_TO_PRINCIPESSINA_UPLOADS)
    os.makedirs(media_type_base_path_abs, exist_ok=True) 
    all_custom_folders = utils.get_custom_folders(media_type_base_path_abs)
    copy_form.target_custom_folder.choices = [(f, f) for f in all_custom_folders]
    if request.method == 'POST':
        if request.form.get('form_type') == 'upload_photo' and photo_form.validate_on_submit():
            file = photo_form.photo_file.data; title = photo_form.title.data; db_custom_folder_name = current_folder_name
            if current_folder_name:
                target_dir_for_upload_abs = os.path.join(media_type_base_path_abs, "custom", current_folder_name)
                s_p_f_db = os.path.join(PRINCIPESSINA_UPLOAD_BASE_DIR_REL_TO_STATIC_UPLOADS, PHOTO_DIR_REL_TO_PRINCIPESSINA_UPLOADS, "custom", current_folder_name)
            else:
                now = datetime.now(); y, m, w = now.year, now.month, now.isocalendar()[1]
                y_w_p_part = utils.ensure_media_folder_structure(get_principessina_base_upload_path_abs(), "photos", y, m, w)
                target_dir_for_upload_abs = os.path.join(get_principessina_base_upload_path_abs(), y_w_p_part)
                s_p_f_db = os.path.join(PRINCIPESSINA_UPLOAD_BASE_DIR_REL_TO_STATIC_UPLOADS, y_w_p_part); db_custom_folder_name = None
            os.makedirs(target_dir_for_upload_abs, exist_ok=True)
            try:
                s_f = save_uploaded_file(file, target_dir_for_upload_abs, utils.ALLOWED_PHOTO_EXTS, utils.MAX_MEDIA_SIZE)
                s_f_db = os.path.join(s_p_f_db, s_f)
                utils.add_media_entry(user['username'], "photo", file.filename, s_f_db, title, db_custom_folder_name)
                flash("写真をアップロードしました。", "success")
            except ValueError as e: flash(str(e), "danger")
            return redirect(url_for('.photo_page', current_folder=current_folder_name))
        elif request.form.get('form_type') == 'create_folder' and folder_form.validate_on_submit():
            n_f_n = folder_form.folder_name.data; success, message = utils.create_custom_media_folder(media_type_base_path_abs, n_f_n) 
            flash(message, "success" if success else "danger")
            return redirect(url_for('.photo_page', current_folder=n_f_n if success else current_folder_name))
    media_entries = utils.get_media_entries(media_type="photo", custom_folder_name=current_folder_name)
    media_entries.sort(key=lambda x: x.get("upload_timestamp", ""), reverse=True)
    current_folder_display_name = current_folder_name if current_folder_name else "年月フォルダ"
    return render_template("decima_photo_page.html", photo_form=photo_form, folder_form=folder_form, copy_form=copy_form, 
        photo_entries=media_entries, custom_photo_folders=all_custom_folders, all_custom_photo_folders=all_custom_folders, 
        current_folder_name=current_folder_name, current_folder_display_name=current_folder_display_name, user=user)

@bp.route('/media/<int:media_id>/copy_to_folder', methods=['POST'])
def copy_media_to_folder(media_id: int):
    user = session.get("user"); form = CopyMediaToCustomFolderForm(request.form) 
    media_type = request.form.get('media_type'); source_folder = request.form.get('source_folder') 
    if media_type == "video": media_type_base_path_abs = os.path.join(get_principessina_base_upload_path_abs(), VIDEO_DIR_REL_TO_PRINCIPESSINA_UPLOADS)
    elif media_type == "photo": media_type_base_path_abs = os.path.join(get_principessina_base_upload_path_abs(), PHOTO_DIR_REL_TO_PRINCIPESSINA_UPLOADS)
    else: flash("無効なメディアタイプです。", "danger"); return redirect(url_for(".index"))
    all_custom_folders = utils.get_custom_folders(media_type_base_path_abs)
    form.target_custom_folder.choices = [(f, f) for f in all_custom_folders]
    if form.validate_on_submit():
        target_folder = form.target_custom_folder.data
        success = utils.add_media_reference_to_custom_folder(media_id, target_folder)
        if success: flash(f"メディアをフォルダ「{target_folder}」にコピーしました。", "success")
        else: flash("メディアのコピーに失敗しました。", "warning")
    else:
        for field, errors in form.errors.items(): flash(f"エラー ({getattr(form, field).label.text}): {', '.join(errors)}", "danger")
    if media_type == "video": return redirect(url_for('.video_page', current_folder=source_folder if source_folder else None))
    if media_type == "photo": return redirect(url_for('.photo_page', current_folder=source_folder if source_folder else None))
    return redirect(url_for(".index"))

@bp.route('/media/<int:media_id>/remove_reference', methods=['POST'])
def remove_media_reference(media_id: int):
    user = session.get("user"); folder_to_remove = request.form.get('folder_to_remove')
    media_type = request.form.get('media_type')
    if not folder_to_remove: flash("削除対象のフォルダが指定されていません。", "danger")
    else:
        success = utils.remove_media_reference_from_custom_folder(media_id, folder_to_remove)
        if success: flash(f"フォルダ「{folder_to_remove}」からのメディア参照を削除しました。", "success")
        else: flash("メディア参照の削除に失敗しました。", "warning")
    rtf = folder_to_remove 
    if media_type == "video": return redirect(url_for('.video_page', current_folder=rtf))
    if media_type == "photo": return redirect(url_for('.photo_page', current_folder=rtf))
    return redirect(url_for(".index"))

@bp.route('/download_media/<path:filepath_in_json>')
def download_media_file(filepath_in_json: str):
    directory = os.path.join(current_app.static_folder, 'uploads')
    return send_from_directory(directory, filepath_in_json, as_attachment=True)

@bp.route('/delete_media/<int:media_id>', methods=['POST'])
def delete_media(media_id: int):
    user = session.get("user")
    if user.get("role") != "admin":
        flash("権限がありません。", "danger"); return redirect(request.referrer or url_for('.index'))
    base_static_uploads_abs = os.path.join(current_app.static_folder, 'uploads')
    media_entries_list = utils.load_media_entries() 
    entry_to_delete = next((e for e in media_entries_list if e.get("id") == media_id), None)
    redirect_url = url_for('.index') 
    if entry_to_delete:
        media_type = entry_to_delete.get('media_type'); source_folder = request.form.get('source_folder') 
        if media_type == 'video': redirect_url = url_for('.video_page', current_folder=source_folder if source_folder else None)
        elif media_type == 'photo': redirect_url = url_for('.photo_page', current_folder=source_folder if source_folder else None)
    if utils.delete_media_entry(media_id, base_static_uploads_abs): flash("メディアファイルを削除しました。", "success")
    else: flash("メディアファイルの削除に失敗しました。", "danger")
    return redirect(redirect_url)
