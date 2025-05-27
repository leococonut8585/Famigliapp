"""Forms for Quest Box blueprint."""

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    TextAreaField,
    SubmitField,
    DateField,
    IntegerField,
    SelectMultipleField,
    widgets,
)
from wtforms.validators import DataRequired, Optional, NumberRange


class MultiCheckboxField(SelectMultipleField):
    """Render multiple choices as checkboxes."""

    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class QuestForm(FlaskForm):
    """Form to create a quest request."""

    title = StringField("タイトル", validators=[DataRequired()])
    body = TextAreaField("内容", validators=[DataRequired()])
    conditions = TextAreaField("参加条件", validators=[Optional()])
    capacity = IntegerField(
        "募集人数", validators=[Optional(), NumberRange(min=0)], default=0
    )
    due_date = DateField("期限", validators=[Optional()])
    assigned_to = MultiCheckboxField("対象ユーザー", validators=[Optional()], coerce=str)
    reward = StringField("報酬", validators=[Optional()])
    submit = SubmitField("投稿")


class RewardForm(FlaskForm):
    """Form to register reward for a quest."""

    reward = StringField("報酬", validators=[Optional()])
    submit = SubmitField("保存")
