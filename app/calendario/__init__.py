"""Calendario blueprint."""

from flask import Blueprint


bp = Blueprint(
    "calendario",
    __name__,
    url_prefix="/calendario",
    template_folder="templates/calendario",
)

from . import routes  # noqa: E402,F401

