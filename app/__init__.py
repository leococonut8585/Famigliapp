"""Application factory for the Famigliapp web interface."""

from typing import Optional


def create_app() -> "Flask":
    """Create and configure :class:`~flask.Flask` instance."""

    from flask import Flask, render_template, session

    app = Flask(__name__)
    app.config.from_object("config")

    from .auth import bp as auth_bp

    app.register_blueprint(auth_bp)

    @app.route("/")
    def index():
        """Simple index page showing login state."""
        user = session.get("user")
        return render_template("index.html", user=user)

    return app


# Optional global for Werkzeug scripts
app: Optional["Flask"] = None

