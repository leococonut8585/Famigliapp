"""Resoconto blueprint setup."""

from flask import Blueprint

bp = Blueprint(
    'resoconto',
    __name__,
    url_prefix='/resoconto',
    template_folder='templates/resoconto',
)

from . import routes  # noqa: E402
