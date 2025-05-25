from flask import Blueprint

bp = Blueprint('intrattenimento', __name__, url_prefix='/intrattenimento')

from . import routes  # noqa: E402
