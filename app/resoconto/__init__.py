"""Resoconto blueprint setup."""

from flask import Blueprint

bp = Blueprint('resoconto', __name__, url_prefix='/resoconto')

from . import routes  # noqa: E402
