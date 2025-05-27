from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import StringField, TextAreaField, SubmitField, FileField
from wtforms.validators import DataRequired, Optional

from app.validators import FileSize
from . import utils


class AddMonsignoreForm(FlaskForm):
    body = TextAreaField("本文", validators=[DataRequired()])
    image = FileField(
        "画像",
        validators=[
            Optional(),
            FileAllowed(utils.ALLOWED_EXTS, "許可されていないファイル形式です"),
            FileSize(utils.MAX_SIZE),
        ],
    )
    submit = SubmitField("投稿")


class MonsignoreFilterForm(FlaskForm):
    author = StringField("投稿者", validators=[Optional()])
    keyword = StringField("キーワード", validators=[Optional()])
    submit = SubmitField("絞り込み")
