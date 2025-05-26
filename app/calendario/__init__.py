"""Calendario blueprint."""

from flask import Blueprint


bp = Blueprint("calendario", __name__, url_prefix="/calendario")

from . import routes  # noqa: E402,F401

