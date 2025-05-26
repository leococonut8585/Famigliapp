"""WSGI entry point for running the Flask application."""

from app import create_app
from app.resoconto.tasks import start_scheduler

app = create_app()
start_scheduler()

