from flask import render_template, session, redirect, url_for, flash, request

from . import bp
import config
from .forms import PollForm, VoteForm
from . import utils


@bp.before_request
def require_login():
    if 'user' not in session:
        return redirect(url_for('auth.login', next=request.url))


@bp.route('/')
def index():
    user = session.get('user')
    return render_template('vote_index.html', user=user)


@bp.route('/open')
def open_list():
    user = session.get('user')
    polls = [p for p in utils.load_polls() if p.get('status') == 'open']
    return render_template('vote_open_list.html', polls=polls, user=user)


@bp.route('/closed')
def closed_list():
    user = session.get('user')
    polls = [p for p in utils.load_polls() if p.get('status') == 'closed']
    return render_template('vote_closed_list.html', polls=polls, user=user)


@bp.route('/create', methods=['GET', 'POST'])
def create():
    user = session.get('user')
    form = PollForm()
    form.targets.choices = [(u, u) for u in config.USERS.keys()]
    if form.validate_on_submit():
        options = [o.strip() for o in form.options.data if o.strip()]
        utils.add_poll(
            user['username'], form.title.data, options, form.targets.data
        )
        flash('投稿しました')
        return redirect(url_for('vote_box.open_list'))
    return render_template('vote_form.html', form=form, user=user)


@bp.route('/vote/<int:poll_id>', methods=['GET', 'POST'])
def vote(poll_id: int):
    user = session.get('user')
    polls = utils.load_polls()
    poll = next((p for p in polls if p.get('id') == poll_id), None)
    if not poll or poll.get('status') != 'open':
        flash('該当IDがありません')
        return redirect(url_for('vote_box.open_list'))
    form = VoteForm()
    form.choice.choices = [(str(i), o) for i, o in enumerate(poll['options'])]
    if form.validate_on_submit():
        utils.add_vote(poll_id, user['username'], int(form.choice.data))
        flash('投票しました')
        return redirect(url_for('vote_box.open_list'))
    voted = poll.get('votes', {}).get(user['username'])
    return render_template('vote_detail.html', poll=poll, form=form, voted=voted, user=user)


@bp.route('/close/<int:poll_id>')
def close(poll_id: int):
    user = session.get('user')
    polls = utils.load_polls()
    poll = next((p for p in polls if p.get('id') == poll_id), None)
    if not poll:
        flash('該当IDがありません')
        return redirect(url_for('vote_box.open_list'))
    if user['role'] != 'admin' and poll.get('author') != user['username']:
        flash('権限がありません')
        return redirect(url_for('vote_box.open_list'))
    utils.close_poll(poll_id)
    flash('締め切りました')
    return redirect(url_for('vote_box.closed_list'))
