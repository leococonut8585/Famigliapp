"""Forms for Calendario blueprint."""

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    DateField,
    TextAreaField,
    SubmitField,
    SelectField,
    SelectMultipleField,
)
from wtforms.validators import DataRequired, Optional
import config


class EventForm(FlaskForm):
    """Form to create or edit an event."""

    date = DateField("日付", validators=[DataRequired()])
    title = StringField("タイトル", validators=[DataRequired()])
    description = TextAreaField("内容", validators=[Optional()])
    employee = StringField("従業員", validators=[Optional()])
    category = SelectField(
        "種類",
        choices=[
            ("shift", "シフト"),
            ("lesson", "レッスン"),
            ("hug", "ハグの日"),
            ("other", "その他"),
        ],
        validators=[DataRequired()],
    )
    participants = SelectMultipleField(
        "対象者",
        choices=[(u, u) for u in config.USERS if u not in config.EXCLUDED_USERS],
        validators=[Optional()],
    )
    submit = SubmitField("保存")


class StatsForm(FlaskForm):
    """Form to filter statistics by date range."""

    start = DateField("開始日", validators=[Optional()])
    end = DateField("終了日", validators=[Optional()])
    submit = SubmitField("表示")

