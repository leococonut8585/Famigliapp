"""Blueprint definition for Principessina module."""

from flask import Blueprint


bp = Blueprint("principessina", __name__, url_prefix="/principessina")


from . import routes  # noqa: E402

