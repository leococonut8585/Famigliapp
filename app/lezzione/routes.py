"""Routes for Lezzione blueprint."""

from flask import render_template, session, redirect, url_for, flash, request

from . import bp
from .forms import LessonScheduleForm, LessonFeedbackForm
from . import utils # Assuming utils will be adapted or might not be used by these basic routes yet


@bp.before_request
def require_login():
    if "user" not in session:
        return redirect(url_for("auth.login", next=request.url))


@bp.route("/top") # MODIFIED route
def seminario_top(): # MODIFIED function name
    user = session.get("user")
    # entries = utils.load_entries() # Logic for entries might change or be removed for a simple top page
    # entries.sort(key=lambda e: e.get("lesson_date"))
    return render_template("seminario_top.html", user=user) # MODIFIED template


@bp.route('/view')
def view_seminarii():
    user = session.get("user")
    # Logic to fetch seminarii will be added later
    return render_template('view_seminario.html', user=user)


@bp.route('/feedback', methods=['GET', 'POST'])
def submit_seminario_feedback():
    user = session.get("user")
    # Form handling logic will be added later
    # For now, just render the template for GET requests
    return render_template('submit_feedback.html', user=user)


@bp.route('/completed')
def completed_seminarii():
    user = session.get("user")
    # Logic to fetch completed seminarii will be added later
    return render_template('completed_seminario.html', user=user)

# Old Lezzione routes /schedule and /feedback/<id> are removed.
# The new /feedback route is for Seminario.

