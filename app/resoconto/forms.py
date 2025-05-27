from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, DateField
from wtforms.validators import DataRequired


class ResocontoForm(FlaskForm):
    """Form for submitting a work report."""

    date = DateField("日付", validators=[DataRequired()])
    work = TextAreaField("業務内容", validators=[DataRequired()])
    issue = TextAreaField("感じた課題", validators=[DataRequired()])
    success = TextAreaField("うまくいったこと", validators=[DataRequired()])
    failure = TextAreaField("失敗したこと", validators=[DataRequired()])
    submit = SubmitField("報告する")
