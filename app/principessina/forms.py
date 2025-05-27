"""Forms for Principessina blueprint."""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import StringField, TextAreaField, SubmitField, FileField
from wtforms.validators import DataRequired, Optional

from app.validators import FileSize
from . import utils


class AddPrincipessinaForm(FlaskForm):
    """Form to add a Principessina post."""

    body = TextAreaField("本文", validators=[DataRequired()])
    attachment = FileField(
        "添付ファイル",
        validators=[
            Optional(),
            FileAllowed(utils.ALLOWED_EXTS, "許可されていないファイル形式です"),
            FileSize(utils.MAX_SIZE),
        ],
    )
    submit = SubmitField("投稿")


class PrincipessinaFilterForm(FlaskForm):
    """Form to filter Principessina posts."""

    author = StringField("投稿者", validators=[Optional()])
    keyword = StringField("キーワード", validators=[Optional()])
    submit = SubmitField("絞り込み")

