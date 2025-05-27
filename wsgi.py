"""WSGI entry point for running the Flask application."""

from app import create_app
from app.resoconto.tasks import start_scheduler
from app.lezzione.tasks import start_scheduler as start_lezzione_scheduler
from app.intrattenimento.tasks import (
    start_scheduler as start_intrattenimento_scheduler,
)
from app.principessina.tasks import (
    start_scheduler as start_principessina_scheduler,
)

app = create_app()
start_scheduler()
start_intrattenimento_scheduler()
start_lezzione_scheduler()
start_principessina_scheduler()

