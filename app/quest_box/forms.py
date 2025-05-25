"""Forms for Quest Box blueprint."""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional


class QuestForm(FlaskForm):
    """Form to create a quest request."""

    title = StringField("タイトル", validators=[DataRequired()])
    body = TextAreaField("内容", validators=[DataRequired()])
    submit = SubmitField("投稿")


class RewardForm(FlaskForm):
    """Form to register reward for a quest."""

    reward = StringField("報酬", validators=[Optional()])
    submit = SubmitField("保存")
