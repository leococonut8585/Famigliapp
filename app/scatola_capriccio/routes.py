from flask import render_template, session, redirect, url_for, flash, request

from . import bp, utils
from .forms import FeedbackForm


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
