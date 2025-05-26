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
from werkzeug.utils import secure_filename

from . import bp
from .forms import AddIntrattenimentoForm, IntrattenimentoFilterForm
from . import utils

UPLOAD_FOLDER = os.path.join('static', 'uploads')


@bp.before_request
def require_login():
    if 'user' not in session:
        return redirect(url_for('auth.login', next=request.url))


@bp.route('/')
def index():
    user = session.get('user')
    form = IntrattenimentoFilterForm(request.args)
    include_expired = user.get('role') == 'admin'
    start_dt = (
        datetime.combine(form.start_date.data, datetime.min.time())
        if form.start_date.data
        else None
    )
    end_dt = (
        datetime.combine(form.end_date.data, datetime.max.time())
        if form.end_date.data
        else None
    )
    posts = utils.filter_posts(
        author=form.author.data or '',
        keyword=form.keyword.data or '',
        include_expired=include_expired,
        start=start_dt,
        end=end_dt,
    )
    return render_template(
        'intrattenimento/intrattenimento_list.html',
        posts=posts,
        form=form,
        user=user,
    )


@bp.route('/add', methods=['GET', 'POST'])
def add():
    user = session.get('user')
    form = AddIntrattenimentoForm()
    if form.validate_on_submit():
        filename = None
        if form.attachment.data and form.attachment.data.filename:
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            filename = secure_filename(form.attachment.data.filename)
            path = os.path.join(UPLOAD_FOLDER, filename)
            form.attachment.data.save(path)
        utils.add_post(
            user['username'],
            form.title.data,
            form.body.data,
            form.end_date.data,
            filename,
        )
        flash('投稿しました')
        return redirect(url_for('intrattenimento.index'))
    return render_template('intrattenimento/intrattenimento_post_form.html', form=form, user=user)


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
