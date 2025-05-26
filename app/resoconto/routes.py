from flask import Blueprint, render_template, session, redirect, url_for, flash, request
from datetime import date
from .forms import ResocontoForm
from . import utils

bp = Blueprint('resoconto', __name__, url_prefix='/resoconto')


@bp.before_request
def require_login():
    if 'user' not in session:
        return redirect(url_for('auth.login', next=request.url))


@bp.route('/')
def index():
    user = session.get('user')
    reports = utils.load_reports()
    if user.get('role') == 'admin':
        view_reports = reports
    else:
        view_reports = [r for r in reports if r.get('author') == user.get('username')]
    return render_template('resoconto/resoconto_admin_dashboard.html' if user.get('role') == 'admin' else 'resoconto/resoconto_my_history.html', reports=view_reports, user=user)


@bp.route('/add', methods=['GET', 'POST'])
def add():
    user = session.get('user')
    form = ResocontoForm()
    if form.validate_on_submit():
        utils.add_report(user['username'], form.date.data, form.body.data)
        flash('投稿しました')
        return redirect(url_for('resoconto.index'))
    return render_template('resoconto/resoconto_submit_form.html', form=form, user=user)


@bp.route('/delete/<int:report_id>')
def delete(report_id: int):
    user = session.get('user')
    if user.get('role') != 'admin':
        flash('権限がありません')
        return redirect(url_for('resoconto.index'))
    if utils.delete_report(report_id):
        flash('削除しました')
    else:
        flash('該当IDがありません')
    return redirect(url_for('resoconto.index'))


@bp.route('/rankings')
def rankings():
    """管理者向けの報告数ランキング表示。"""
    user = session.get('user')
    if user.get('role') != 'admin':
        flash('権限がありません')
        return redirect(url_for('resoconto.index'))

    start_s = request.args.get('start', '')
    end_s = request.args.get('end', '')
    start = end = None
    try:
        if start_s:
            start = date.fromisoformat(start_s)
        if end_s:
            end = date.fromisoformat(end_s)
    except ValueError:
        flash('日付の形式が正しくありません')
        return redirect(url_for('resoconto.index'))

    ranking = utils.get_ranking(start=start, end=end)
    return render_template('resoconto/resoconto_ranking.html', ranking=ranking, user=user)
