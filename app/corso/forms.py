"""Forms for Corso blueprint."""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import (
    StringField,
    TextAreaField,
    SubmitField,
    DateField,
    FileField,
    SelectField,
)
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


class FeedbackForm(FlaskForm):
    """Form to submit feedback for a Corso."""

    corso_id = SelectField("Corso", coerce=int)
    body = TextAreaField("感想", validators=[DataRequired()])
    submit = SubmitField("投稿")

