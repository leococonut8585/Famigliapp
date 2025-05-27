"""Blueprint definition for the Bravissimo module."""

from flask import Blueprint


bp = Blueprint("bravissimo", __name__, url_prefix="/bravissimo")

# Import routes so that they are registered with the blueprint
from . import routes  # noqa: E402
