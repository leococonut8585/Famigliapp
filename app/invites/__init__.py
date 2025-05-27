"""Blueprint for invite code management."""

from flask import Blueprint

bp = Blueprint(
    "invites",
    __name__,
    url_prefix="/invites",
    template_folder="templates/invites",
)

from . import routes  # noqa: E402
