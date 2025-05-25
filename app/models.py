"""Database models for Famigliapp."""

from datetime import datetime

from . import db


if db is not None:  # pragma: no cover - optional dependency

    class User(db.Model):
        """User account."""

        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True, nullable=False)
        email = db.Column(db.String(120), unique=True, nullable=False)
        role = db.Column(db.String(20), default="user")
        password = db.Column(db.String(128), nullable=True)
        points_a = db.Column(db.Integer, default=0)
        points_o = db.Column(db.Integer, default=0)

        def __repr__(self) -> str:  # pragma: no cover - repr helper
            return f"<User {self.username}>"


    class Post(db.Model):
        """Post entry."""

        id = db.Column(db.Integer, primary_key=True)
        author_id = db.Column(db.Integer, db.ForeignKey("user.id"))
        category = db.Column(db.String(80))
        text = db.Column(db.Text)
        timestamp = db.Column(db.DateTime, default=datetime.utcnow)

        author = db.relationship("User", backref=db.backref("posts", lazy=True))

        def __repr__(self) -> str:  # pragma: no cover - repr helper
            return f"<Post {self.id}>"


    class PointsHistory(db.Model):
        """History of point changes."""

        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
        delta_a = db.Column(db.Integer, default=0)
        delta_o = db.Column(db.Integer, default=0)
        timestamp = db.Column(db.DateTime, default=datetime.utcnow)

        user = db.relationship("User", backref=db.backref("points_history", lazy=True))

        def __repr__(self) -> str:  # pragma: no cover - repr helper
            return f"<PointsHistory {self.id}>"

