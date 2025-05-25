try:
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    from flask_migrate import Migrate
except ModuleNotFoundError:  # Packages may not be installed in minimal env
    Flask = None
    SQLAlchemy = None
    Migrate = None

class _Dummy:
    def __getattr__(self, name):
        raise RuntimeError("Flask is required to use database features")

# Initialize extensions

if SQLAlchemy:
    db = SQLAlchemy()
    migrate = Migrate()
else:
    db = _Dummy()
    migrate = _Dummy()


def create_app():
    if Flask is None:
        raise RuntimeError("Flask is not installed")

    app = Flask(__name__)
    app.config.from_object('config')

    db.init_app(app)
    migrate.init_app(app, db)

    return app
