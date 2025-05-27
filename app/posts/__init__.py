"""Blueprint for posts management."""

from flask import Blueprint

bp = Blueprint(
    "posts",
    __name__,
    url_prefix="/posts",
    template_folder="templates/posts",
)

from . import routes  # noqa: E402
