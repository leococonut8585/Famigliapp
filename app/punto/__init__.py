"""Blueprint for points management (Punto)."""

from flask import Blueprint

bp = Blueprint("punto", __name__, url_prefix="/punto")

from . import routes  # noqa: E402
