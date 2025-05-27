from flask import Blueprint

bp = Blueprint(
    'nedari_box',
    __name__,
    url_prefix='/nedari_box',
    template_folder='templates/nedari_box'
)

from . import routes  # noqa: E402
