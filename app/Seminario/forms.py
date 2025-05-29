"""Forms for Seminario blueprint."""

from flask_wtf import FlaskForm
from wtforms import DateField, StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired


class LessonScheduleForm(FlaskForm):
    """Form to register lesson schedule."""

    date = DateField("受講予定日", validators=[DataRequired()])
    title = StringField("レッスン名", validators=[DataRequired()])
    submit = SubmitField("登録")


class LessonFeedbackForm(FlaskForm):
    """Form to submit lesson feedback."""

    body = TextAreaField("感想", validators=[DataRequired()])
    submit = SubmitField("投稿")

