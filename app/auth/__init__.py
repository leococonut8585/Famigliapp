"""Authentication blueprint setup."""

from flask import Blueprint


bp = Blueprint("auth", __name__, url_prefix="/auth")


from . import routes  # noqa: E402

