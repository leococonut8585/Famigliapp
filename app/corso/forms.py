"""Forms for Corso blueprint."""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import StringField, TextAreaField, SubmitField, DateField, FileField
from wtforms.validators import DataRequired, Optional

from app.validators import FileSize
from . import utils


class AddCorsoForm(FlaskForm):
    """Form to add a Corso post."""

    title = StringField("タイトル", validators=[DataRequired()])
    body = TextAreaField("本文", validators=[DataRequired()])
    end_date = DateField("公開終了日", validators=[Optional()])
    attachment = FileField(
        "添付ファイル",
        validators=[
            Optional(),
            FileAllowed(utils.ALLOWED_EXTS, "許可されていないファイル形式です"),
            FileSize(utils.MAX_SIZE),
        ],
    )
    submit = SubmitField("投稿")


class CorsoFilterForm(FlaskForm):
    """Form to filter Corso posts."""

    author = StringField("投稿者", validators=[Optional()])
    keyword = StringField("キーワード", validators=[Optional()])
    submit = SubmitField("絞り込み")

