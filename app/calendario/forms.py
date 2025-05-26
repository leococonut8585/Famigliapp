"""Forms for Calendario blueprint."""

from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional


class EventForm(FlaskForm):
    """Form to create or edit an event."""

    date = DateField("日付", validators=[DataRequired()])
    title = StringField("タイトル", validators=[DataRequired()])
    description = TextAreaField("内容", validators=[Optional()])
    submit = SubmitField("保存")

