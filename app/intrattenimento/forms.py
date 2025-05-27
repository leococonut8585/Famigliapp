from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import (
    StringField,
    TextAreaField,
    SubmitField,
    DateField,
    FileField,
    SelectField,
)
from wtforms.validators import DataRequired, Optional, Length

from app.validators import FileSize
from . import utils


class AddIntrattenimentoForm(FlaskForm):
    title = StringField('タイトル', validators=[DataRequired()])
    body = TextAreaField('本文', validators=[DataRequired()])
    end_date = DateField('公開終了日', validators=[Optional()])
    attachment = FileField(
        '添付ファイル',
        validators=[
            Optional(),
            FileAllowed(utils.ALLOWED_EXTS, '許可されていないファイル形式です'),
            FileSize(utils.MAX_SIZE),
        ],
    )
    submit = SubmitField('投稿')

class AddTaskForm(FlaskForm):
    """Form to create an entertainment task."""

    title = StringField('タイトル', validators=[DataRequired()])
    body = TextAreaField('解説', validators=[DataRequired()])
    due_date = DateField('感想投稿期限', validators=[Optional()])
    video = FileField(
        '動画',
        validators=[
            Optional(),
            FileAllowed(utils.ALLOWED_EXTS, '許可されていないファイル形式です'),
            FileSize(utils.MAX_VIDEO_SIZE),
        ],
    )
    submit = SubmitField('追加')


class FeedbackForm(FlaskForm):
    """Form to submit feedback for a task."""

    task_id = SelectField('課題', coerce=int, validators=[DataRequired()])
    body = TextAreaField(
        '感想', validators=[DataRequired(), Length(min=300, message='短すぎるね、300文字以上になるようにもう少し集中したほうが良い')]
    )
    submit = SubmitField('送信')
