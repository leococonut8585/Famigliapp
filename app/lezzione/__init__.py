"""Blueprint for Lezzione lesson feedback."""

from flask import Blueprint


bp = Blueprint(
    "lezzione",
    __name__,
    url_prefix="/lezzione",
    template_folder="templates/lezzione",
)


from . import routes  # noqa: E402

