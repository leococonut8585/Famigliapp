from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, FileField
from wtforms.validators import DataRequired, Optional


class AddMonsignoreForm(FlaskForm):
    body = TextAreaField("本文", validators=[DataRequired()])
    image = FileField("画像", validators=[Optional()])
    submit = SubmitField("投稿")


class MonsignoreFilterForm(FlaskForm):
    author = StringField("投稿者", validators=[Optional()])
    keyword = StringField("キーワード", validators=[Optional()])
    submit = SubmitField("絞り込み")
