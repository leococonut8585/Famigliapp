"""Forms for Seminario blueprint."""

from flask_wtf import FlaskForm
from wtforms import DateField, StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired


class LessonScheduleForm(FlaskForm):
    """Form to register lesson schedule."""

    date = DateField("開始日", validators=[DataRequired()]) # Changed label from "受講予定日"
    title = StringField("タイトル", validators=[DataRequired()]) # Changed label from "レッスン名"
    seminar_end_date = DateField("終了日", validators=[DataRequired()])
    calendar_event_type = SelectField(
        "種別",
        choices=[('kouza', '講座')],
        default='kouza',
        validators=[DataRequired()]
    )
    submit = SubmitField("登録")


class LessonFeedbackForm(FlaskForm):
    """Form to submit lesson feedback."""

    body = TextAreaField("感想", validators=[DataRequired()])
    submit = SubmitField("投稿")

