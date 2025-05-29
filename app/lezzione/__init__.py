"""Blueprint for Lezzione lesson feedback."""

from flask import Blueprint


bp = Blueprint(
    "seminario",
    __name__,
    url_prefix="/seminario",
    template_folder="templates/seminario",
)


from . import routes  # noqa: E402

