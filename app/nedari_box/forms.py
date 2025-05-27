from flask_wtf import FlaskForm
from wtforms import (
    TextAreaField,
    SubmitField,
    SelectMultipleField,
    SelectField,
    widgets,
)
from wtforms.validators import DataRequired


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class NedariForm(FlaskForm):
    body = TextAreaField('内容', validators=[DataRequired()])
    targets = MultiCheckboxField('対象ユーザー', validators=[DataRequired()], coerce=str)
    visibility = SelectField(
        '公開範囲',
        choices=[('all', '全員閲覧可能'), ('admins', 'シニョーレとレディのみ閲覧可能')]
    )
    submit = SubmitField('投稿')
