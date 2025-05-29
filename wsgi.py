"""WSGI entry point for running the Flask application."""

from app import create_app
from app.resoconto.tasks import start_scheduler
from app.seminario.tasks import start_scheduler as start_seminario_scheduler
from app.corso.tasks import start_scheduler as start_corso_scheduler
from app.intrattenimento.tasks import (
    start_scheduler as start_intrattenimento_scheduler,
)
from app.principessina.tasks import (
    start_scheduler as start_principessina_scheduler,
)

app = create_app()
start_scheduler()
start_intrattenimento_scheduler()
start_seminario_scheduler()
start_principessina_scheduler()
start_corso_scheduler()

