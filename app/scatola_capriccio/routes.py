from flask import render_template, session, redirect, url_for, flash, request

from . import bp, utils
from .forms import FeedbackForm, SurveyForm


@bp.before_request
def require_login():
    if 'user' not in session:
        return redirect(url_for('auth.login', next=request.url))


@bp.route('/')
def index():
    user = session.get('user')
    if user.get('role') != 'admin':
        flash('権限がありません')
        return redirect(url_for('index'))
    posts = utils.load_posts()
    return render_template(
        'scatola_capriccio/feedback_list_admin.html', posts=posts, user=user
    )


@bp.route('/add', methods=['GET', 'POST'])
def add():
    user = session.get('user')
    form = FeedbackForm()
    if form.validate_on_submit():
        utils.add_post(user['username'], form.body.data)
        flash('投稿しました')
        return redirect(url_for('index'))
    return render_template('scatola_capriccio/feedback_form.html', form=form, user=user)


@bp.route('/survey')
def survey_list():
    user = session.get('user')
    if user.get('role') != 'admin':
        flash('権限がありません')
        return redirect(url_for('index'))
    surveys = utils.load_surveys()
    return render_template('scatola_capriccio/survey_view.html', surveys=surveys, user=user)


@bp.route('/survey/add', methods=['GET', 'POST'])
def survey_add():
    user = session.get('user')
    if user.get('role') != 'admin':
        flash('権限がありません')
        return redirect(url_for('index'))
    form = SurveyForm()
    if form.validate_on_submit():
        targets = [t.strip() for t in (form.targets.data or '').split(',') if t.strip()]
        utils.add_survey(user['username'], form.question.data, targets)
        flash('投稿しました')
        return redirect(url_for('scatola_capriccio.survey_list'))
    return render_template('scatola_capriccio/survey_form_admin.html', form=form, user=user)
