from flask import Blueprint

bp = Blueprint(
    'vote_box',
    __name__,
    url_prefix='/vote_box',
    template_folder='templates/vote_box'
)

from . import routes  # noqa: E402
