from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, DateField
from wtforms.validators import DataRequired


class ResocontoForm(FlaskForm):
    date = DateField('日付', validators=[DataRequired()])
    body = TextAreaField('内容', validators=[DataRequired()])
    submit = SubmitField('投稿')
