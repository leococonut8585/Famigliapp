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
            FileAllowed(utils.POST_ALLOWED_EXTS, "許可されていないファイル形式です"), # Updated to POST_ALLOWED_EXTS
            FileSize(utils.MAX_POST_FILE_SIZE), # Updated to MAX_POST_FILE_SIZE
        ],
    )
    submit = SubmitField("投稿")


# MonsignoreFilterForm has been removed as requested.


class AddKadaiForm(FlaskForm):
    title = StringField("タイトル", validators=[DataRequired()])
    text_body = TextAreaField("本文（任意）", validators=[Optional()])
    attachment = FileField(
        "画像または動画ファイル",
        validators=[
            Optional(),
            FileAllowed(utils.KADAI_ALLOWED_EXTS, "許可されていないファイル形式です"),
            FileSize(utils.MAX_KADAI_FILE_SIZE)
        ]
    )
    submit = SubmitField("投稿")
