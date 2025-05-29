"""Blueprint definition for the Monsignore module."""

from flask import Blueprint

bp = Blueprint(
    "monsignore",
    __name__,
    url_prefix="/monsignore",
    template_folder="templates/monsignore",
)

# Import routes so that they are registered with the blueprint
from . import routes  # noqa: E402

from . import tasks
if tasks.scheduler is not None: # Ensure scheduler was initialized
    tasks.start_scheduler()
