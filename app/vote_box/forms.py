from flask_wtf import FlaskForm
from wtforms import RadioField, StringField, TextAreaField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired
import config


class PollForm(FlaskForm):
    title = StringField('タイトル', validators=[DataRequired()])
    options = TextAreaField('選択肢(1行に1つ)', validators=[DataRequired()])
    targets = SelectMultipleField('対象ユーザー', choices=[(u, u) for u in config.USERS.keys()])
    submit = SubmitField('公開する')

class VoteForm(FlaskForm):
    choice = RadioField("選択", validators=[DataRequired()])
    submit = SubmitField("投票")
