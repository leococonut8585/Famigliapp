from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, StringField
from wtforms.validators import DataRequired, Optional


class FeedbackForm(FlaskForm):
    body = TextAreaField("内容", validators=[DataRequired()])
    submit = SubmitField("投稿")


class SurveyForm(FlaskForm):
    question = TextAreaField("質問", validators=[DataRequired()])
    targets = StringField("対象ユーザー(カンマ区切り)", validators=[Optional()])
    submit = SubmitField("投稿")
