"""Application factory for the Famigliapp web interface."""

from typing import Optional

try:
    from flask_sqlalchemy import SQLAlchemy
    from flask_migrate import Migrate
except Exception:  # pragma: no cover - optional dependency
    SQLAlchemy = None  # type: ignore
    Migrate = None  # type: ignore

db = SQLAlchemy() if SQLAlchemy else None  # type: ignore
_migrate = Migrate() if Migrate else None  # type: ignore


def create_app() -> "Flask":
    """Create and configure :class:`~flask.Flask` instance."""

    from flask import Flask, render_template, session

    app = Flask(__name__)
    app.config.from_object("config")

    if db is not None:
        db.init_app(app)
        if _migrate is not None:
            _migrate.init_app(app, db)

    from .auth import bp as auth_bp
    from .punto import bp as punto_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(punto_bp)

    if db is not None:
        from . import models  # noqa: F401

    @app.route("/")
    def index():
        """Simple index page showing login state."""
        user = session.get("user")
        return render_template("index.html", user=user)

    return app


# Optional global for Werkzeug scripts
app: Optional["Flask"] = None

