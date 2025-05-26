"""Forms for Calendario blueprint."""

from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional


class EventForm(FlaskForm):
    """Form to create or edit an event."""

    date = DateField("日付", validators=[DataRequired()])
    title = StringField("タイトル", validators=[DataRequired()])
    description = TextAreaField("内容", validators=[Optional()])
    employee = StringField("従業員", validators=[Optional()])
    submit = SubmitField("保存")


class StatsForm(FlaskForm):
    """Form to filter statistics by date range."""

    start = DateField("開始日", validators=[Optional()])
    end = DateField("終了日", validators=[Optional()])
    submit = SubmitField("表示")

