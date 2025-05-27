from flask_wtf import FlaskForm
from wtforms import (
    RadioField,
    StringField,
    TextAreaField,
    SubmitField,
    SelectMultipleField,
    FieldList,
)
from wtforms.validators import DataRequired
import config


class PollForm(FlaskForm):
    title = StringField("タイトル", validators=[DataRequired()])
    # FieldList で動的に選択肢を追加できるようにする
    options = FieldList(StringField("選択肢", validators=[DataRequired()]), min_entries=2)
    targets = SelectMultipleField(
        "対象ユーザー", choices=[(u, u) for u in config.USERS.keys()]
    )
    submit = SubmitField("公開する")

class VoteForm(FlaskForm):
    choice = RadioField("選択", validators=[DataRequired()])
    submit = SubmitField("投票")
