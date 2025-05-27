from flask import render_template, session, redirect, url_for, flash, request

from . import bp, utils
from .forms import NedariForm
from app.utils import send_email
import config


@bp.before_request
def require_login():
    if 'user' not in session:
        return redirect(url_for('auth.login', next=request.url))


@bp.route('/')
def index():
    user = session.get('user')
    posts = utils.load_posts()
    if user.get('role') != 'admin':
        posts = [
            p for p in posts
            if p.get('visibility') == 'all' or p.get('author') == user.get('username')
        ]
    return render_template('nedari_list.html', posts=posts, user=user)


@bp.route('/add', methods=['GET', 'POST'])
def add():
    user = session.get('user')
    form = NedariForm()
    valid_users = [u for u in config.USERS.keys() if u not in config.EXCLUDED_USERS]
    form.targets.choices = [(u, u) for u in valid_users]
    if form.validate_on_submit():
        utils.add_post(
            user['username'],
            form.body.data,
            form.targets.data,
            form.visibility.data,
        )
        if form.visibility.data == 'all':
            recipients = config.USERS.keys()
        else:
            recipients = [u for u, info in config.USERS.items() if info.get('role') == 'admin']
        for r in recipients:
            email = config.USERS[r].get('email')
            if email:
                send_email('New Nedari', form.body.data, email)
        flash('投稿しました')
        return redirect(url_for('nedari_box.index'))
    return render_template('nedari_form.html', form=form, user=user)
