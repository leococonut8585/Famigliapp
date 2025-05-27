from datetime import datetime
import os

from flask import (
    render_template,
    session,
    redirect,
    url_for,
    flash,
    request,
    send_from_directory,
)
from app.utils import save_uploaded_file

from . import bp
from .forms import (
    AddIntrattenimentoForm,
    AddTaskForm,
    FeedbackForm,
)
from . import utils

UPLOAD_FOLDER = os.path.join('static', 'uploads')


@bp.before_request
def require_login():
    if 'user' not in session:
        return redirect(url_for('auth.login', next=request.url))


@bp.route('/')
def index():
    user = session.get('user')
    include_expired = user.get('role') == 'admin'
    posts = utils.filter_posts(include_expired=include_expired)
    return render_template(
        'intrattenimento/intrattenimento_list.html',
        posts=posts,
        user=user,
    )


@bp.route('/add', methods=['GET', 'POST'])
def add():
    user = session.get('user')
    form = AddIntrattenimentoForm()
    if form.validate_on_submit():
        filename = None
        if form.attachment.data and form.attachment.data.filename:
            try:
                filename = save_uploaded_file(
                    form.attachment.data,
                    UPLOAD_FOLDER,
                    utils.ALLOWED_EXTS,
                    utils.MAX_SIZE,
                )
            except ValueError as e:
                flash(str(e))
                return render_template(
                    'intrattenimento/intrattenimento_post_form.html',
                    form=form,
                    user=user,
                    allowed_exts=', '.join(utils.ALLOWED_EXTS),
                    max_size=utils.MAX_SIZE,
                )
        utils.add_post(
            user['username'],
            form.title.data,
            form.body.data,
            form.end_date.data,
            filename,
        )
        flash('投稿しました')
        return redirect(url_for('intrattenimento.index'))
    return render_template(
        'intrattenimento/intrattenimento_post_form.html',
        form=form,
        user=user,
        allowed_exts=', '.join(utils.ALLOWED_EXTS),
        max_size=utils.MAX_SIZE,
    )


@bp.route('/delete/<int:post_id>')
def delete(post_id: int):
    user = session.get('user')
    if user.get('role') != 'admin':
        flash('権限がありません')
        return redirect(url_for('intrattenimento.index'))
    if utils.delete_post(post_id):
        flash('削除しました')
    else:
        flash('該当IDがありません')
    return redirect(url_for('intrattenimento.index'))


@bp.route('/download/<path:filename>')
def download(filename: str):
    """添付ファイルのダウンロード。公開期限切れの場合はユーザーには許可しない。"""
    user = session.get('user')
    posts = utils.load_posts()
    for p in posts:
        if p.get('filename') == filename:
            end_date = p.get('end_date')
            if user.get('role') != 'admin' and end_date:
                try:
                    if datetime.fromisoformat(end_date) < datetime.now():
                        flash('公開期間が終了しています')
                        return redirect(url_for('intrattenimento.index'))
                except ValueError:
                    pass
            return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
    flash('ファイルが見つかりません')
    return redirect(url_for('intrattenimento.index'))


@bp.route('/detail/<int:post_id>')
def detail(post_id: int):
    """個別投稿の詳細表示。公開期限切れはユーザーには非表示。"""
    user = session.get('user')
    posts = utils.load_posts()
    for p in posts:
        if p.get('id') == post_id:
            end_date = p.get('end_date')
            if user.get('role') != 'admin' and end_date:
                try:
                    if datetime.fromisoformat(end_date) < datetime.now():
                        flash('公開期間が終了しています')
                        return redirect(url_for('intrattenimento.index'))
                except ValueError:
                    pass
            return render_template(
                'intrattenimento/intrattenimento_detail.html',
                post=p,
                user=user,
            )
    flash('該当IDがありません')
    return redirect(url_for('intrattenimento.index'))


@bp.route('/tasks')
def tasks():
    user = session.get('user')
    tasks = utils.get_active_tasks()
    return render_template('intrattenimento/task_list.html', tasks=tasks, user=user)


@bp.route('/tasks/add', methods=['GET', 'POST'])
def task_add():
    user = session.get('user')
    if user.get('role') != 'admin':
        flash('権限がありません')
        return redirect(url_for('intrattenimento.tasks'))
    form = AddTaskForm()
    if form.validate_on_submit():
        filename = None
        if form.video.data and form.video.data.filename:
            try:
                filename = save_uploaded_file(
                    form.video.data,
                    UPLOAD_FOLDER,
                    utils.ALLOWED_EXTS,
                    utils.MAX_VIDEO_SIZE,
                )
            except ValueError as e:
                flash(str(e))
                return render_template(
                    'intrattenimento/task_add_form.html',
                    form=form,
                    user=user,
                )
        utils.add_task(form.title.data, form.body.data, form.due_date.data, filename)
        flash('追加しました')
        return redirect(url_for('intrattenimento.tasks'))
    return render_template('intrattenimento/task_add_form.html', form=form, user=user)


@bp.route('/tasks/finish/<int:task_id>')
def task_finish(task_id: int):
    user = session.get('user')
    if user.get('role') != 'admin':
        flash('権限がありません')
        return redirect(url_for('intrattenimento.tasks'))
    if utils.finish_task(task_id):
        flash('終了しました')
    else:
        flash('該当IDがありません')
    return redirect(url_for('intrattenimento.tasks'))


@bp.route('/tasks/completed')
def task_completed():
    user = session.get('user')
    tasks = utils.get_finished_tasks()
    return render_template('intrattenimento/task_completed.html', tasks=tasks, user=user)


@bp.route('/tasks/feedback', methods=['GET', 'POST'])
def task_feedback():
    user = session.get('user')
    form = FeedbackForm()
    form.task_id.choices = [(t['id'], t['title']) for t in utils.get_active_tasks()]
    if form.validate_on_submit():
        if utils.add_feedback(form.task_id.data, user['username'], form.body.data):
            flash('投稿しました')
            return redirect(url_for('intrattenimento.tasks'))
        flash('投稿できません')
    return render_template('intrattenimento/feedback_form.html', form=form, user=user)


@bp.route('/tasks/download/<path:filename>')
def task_download(filename: str):
    tasks = utils.load_tasks()
    for t in tasks:
        if t.get('filename') == filename:
            return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)
    flash('ファイルが見つかりません')
    return redirect(url_for('intrattenimento.tasks'))
