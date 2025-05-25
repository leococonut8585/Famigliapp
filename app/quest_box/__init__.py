"""Blueprint for Quest Box management."""

from flask import Blueprint

bp = Blueprint("quest_box", __name__, url_prefix="/quest_box")

from . import routes  # noqa: E402
