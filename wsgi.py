"""WSGI entry point for running the Flask application."""

from app import create_app
from app.resoconto.tasks import start_scheduler
from app.lezzione.tasks import start_scheduler as start_lezzione_scheduler

app = create_app()
start_scheduler()
start_lezzione_scheduler()

