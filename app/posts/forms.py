"""Forms for Posts blueprint."""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional


class AddPostForm(FlaskForm):
    """Form to add a new post."""

    category = StringField("カテゴリ", validators=[Optional()])
    text = TextAreaField("内容", validators=[DataRequired()])
    submit = SubmitField("投稿")


class PostFilterForm(FlaskForm):
    """Form to filter posts."""

    category = StringField("カテゴリ", validators=[Optional()])
    author = StringField("投稿者", validators=[Optional()])
    keyword = StringField("検索語", validators=[Optional()])
    start_date = StringField("開始日", validators=[Optional()])
    end_date = StringField("終了日", validators=[Optional()])
    submit = SubmitField("絞り込み")
