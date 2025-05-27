"""Corso blueprint module."""

from flask import Blueprint

bp = Blueprint(
    "corso",
    __name__,
    url_prefix="/corso",
    template_folder="templates/corso",
)

from . import routes  # noqa: E402

