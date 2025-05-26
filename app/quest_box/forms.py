"""Forms for Quest Box blueprint."""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, DateField
from wtforms.validators import DataRequired, Optional


class QuestForm(FlaskForm):
    """Form to create a quest request."""

    title = StringField("タイトル", validators=[DataRequired()])
    body = TextAreaField("内容", validators=[DataRequired()])
    due_date = DateField("期限", validators=[Optional()])
    assigned_to = StringField("対象ユーザー", validators=[Optional()])
    submit = SubmitField("投稿")


class RewardForm(FlaskForm):
    """Form to register reward for a quest."""

    reward = StringField("報酬", validators=[Optional()])
    submit = SubmitField("保存")
