from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, FileField
from wtforms.validators import DataRequired, Optional


class AddBravissimoForm(FlaskForm):
    text = TextAreaField("内容", validators=[DataRequired()])
    audio = FileField("音声ファイル", validators=[Optional()])
    submit = SubmitField("投稿")


class BravissimoFilterForm(FlaskForm):
    author = StringField("投稿者", validators=[Optional()])
    keyword = StringField("検索語", validators=[Optional()])
    submit = SubmitField("絞り込み")
