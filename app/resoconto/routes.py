from flask import (
    render_template,
    session,
    redirect,
    url_for,
    flash,
    request,
    make_response,
)
import io
import csv
from datetime import date, timedelta
from .forms import ResocontoForm
from . import utils
from . import tasks
from . import claude_utils

from . import bp


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
    return render_template('resoconto_admin_dashboard.html' if user.get('role') == 'admin' else 'resoconto_my_history.html', reports=view_reports, user=user)


@bp.route('/add', methods=['GET', 'POST'])
def add():
    user = session.get('user')
    form = ResocontoForm()
    if form.validate_on_submit():
        report = {
            'work': form.work.data,
            'issue': form.issue.data,
            'success': form.success.data,
            'failure': form.failure.data,
        }
        history = utils.filter_reports(
            author=user['username'],
            start=form.date.data - timedelta(days=30),
            end=form.date.data - timedelta(days=1),
        )
        summary = claude_utils.summarize_report(user['username'], report, history)
        utils.add_report(
            user['username'],
            form.date.data,
            '',
            work=report['work'],
            issue=report['issue'],
            success=report['success'],
            failure=report['failure'],
            claude_summary=summary,
        )
        flash('投稿しました')
        flash(summary)
        return redirect(url_for('resoconto.index'))
    return render_template('resoconto_submit_form.html', form=form, user=user)


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
    return render_template('resoconto_ranking.html', ranking=ranking, user=user)


@bp.route('/analysis')
def analysis():
    """管理者向けのAI分析結果表示。"""
    user = session.get('user')
    if user.get('role') != 'admin':
        flash('権限がありません')
        return redirect(url_for('resoconto.index'))

    ranking, analysis = tasks.analyze_reports()
    return render_template(
        'resoconto_analysis.html',
        ranking=ranking,
        analysis=analysis,
        user=user,
    )


@bp.route('/claude_report')
def claude_report():
    """管理者向けClaude分析結果表示"""
    user = session.get('user')
    if user.get('role') != 'admin':
        flash('権限がありません')
        return redirect(url_for('resoconto.index'))
    reports = utils.load_claude_reports()
    return render_template('resoconto_claude_report.html', reports=reports, user=user)


@bp.route('/export')
def export_csv():
    """報告履歴をCSVダウンロードする。管理者専用。"""

    user = session.get('user')
    if user.get('role') != 'admin':
        flash('権限がありません')
        return redirect(url_for('resoconto.index'))

    reports = utils.load_reports()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        'id',
        'date',
        'author',
        'body',
        'work',
        'issue',
        'success',
        'failure',
        'claude_summary',
        'timestamp',
    ])
    for r in reports:
        writer.writerow([
            r.get('id'),
            r.get('date', ''),
            r.get('author', ''),
            r.get('body', ''),
            r.get('work', ''),
            r.get('issue', ''),
            r.get('success', ''),
            r.get('failure', ''),
            r.get('claude_summary', ''),
            r.get('timestamp', ''),
        ])
    response = make_response(buf.getvalue())
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = 'attachment; filename=resoconto.csv'
    return response

