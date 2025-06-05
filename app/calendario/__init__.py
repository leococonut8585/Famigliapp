"""Calendario blueprint."""

from flask import Blueprint
from . import utils # Assuming utils.py is in the same directory


bp = Blueprint(
    "calendario",
    __name__,
    url_prefix="/calendario",
    template_folder="templates/calendario",
)

# Register the filter
@bp.app_template_filter('initials')
def initials_template_filter(name):
    return utils.another_initials_filter_for_japanese_names(name)

from . import routes  # noqa: E402,F401

