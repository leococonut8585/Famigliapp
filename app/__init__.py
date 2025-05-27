"""Application factory for the Famigliapp web interface."""

from typing import Optional
import os

try:
    from flask_sqlalchemy import SQLAlchemy
    from flask_migrate import Migrate
    from flask_mail import Mail
except Exception:  # pragma: no cover - optional dependency
    SQLAlchemy = None  # type: ignore
    Migrate = None  # type: ignore
    Mail = None  # type: ignore

db = SQLAlchemy() if SQLAlchemy else None  # type: ignore
_migrate = Migrate() if Migrate else None  # type: ignore
mail = Mail() if Mail else None  # type: ignore


def create_app() -> "Flask":
    """Create and configure :class:`~flask.Flask` instance."""

    from flask import Flask, render_template, session

    # ``static`` directory lives at the repository root so point Flask there
    static_folder = os.path.join(os.path.dirname(__file__), "..", "static")
    app = Flask(__name__, static_folder=static_folder)
    app.config.from_object("config")

    if mail is not None:
        mail.init_app(app)

    if db is not None:
        db.init_app(app)
        if _migrate is not None:
            _migrate.init_app(app, db)

    from .auth import bp as auth_bp
    from .punto import bp as punto_bp
    from .posts import bp as posts_bp
    from .bravissimo import bp as bravissimo_bp
    from .intrattenimento import bp as intrattenimento_bp
    from .corso import bp as corso_bp
    from .principessina import bp as principessina_bp
    from .scatola_capriccio import bp as scatola_capriccio_bp
    from .monsignore import bp as monsignore_bp
    from .quest_box import bp as quest_box_bp
    from .nedari_box import bp as nedari_box_bp
    from .invites import bp as invites_bp
    from .calendario import bp as calendario_bp
    from .resoconto import bp as resoconto_bp
    from .lezzione import bp as lezzione_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(punto_bp)
    app.register_blueprint(posts_bp)
    app.register_blueprint(bravissimo_bp)
    app.register_blueprint(intrattenimento_bp)
    app.register_blueprint(corso_bp)
    app.register_blueprint(principessina_bp)
    app.register_blueprint(scatola_capriccio_bp)
    app.register_blueprint(monsignore_bp)
    app.register_blueprint(quest_box_bp)
    app.register_blueprint(nedari_box_bp)
    app.register_blueprint(invites_bp)
    app.register_blueprint(calendario_bp)
    app.register_blueprint(resoconto_bp)
    app.register_blueprint(lezzione_bp)

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

