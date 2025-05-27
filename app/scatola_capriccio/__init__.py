from flask import Blueprint

bp = Blueprint(
    'scatola_capriccio',
    __name__,
    url_prefix='/scatola_capriccio',
    template_folder='templates/scatola_capriccio',
)

from . import routes  # noqa: E402
