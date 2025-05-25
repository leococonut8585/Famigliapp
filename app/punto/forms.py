"""Forms for Punto blueprint."""

from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField, StringField
from wtforms.validators import DataRequired, Optional


class EditPointsForm(FlaskForm):
    """Form to edit a user's points."""

    a = IntegerField("Aポイント", validators=[DataRequired()])
    o = IntegerField("Oポイント", validators=[DataRequired()])
    u = IntegerField("Uポイント", render_kw={"readonly": True})
    submit = SubmitField("保存")


class HistoryFilterForm(FlaskForm):
    """Form to filter points history."""

    username = StringField("ユーザー名", validators=[Optional()])
    start = StringField("開始日(YYYY-MM-DD)", validators=[Optional()])
    end = StringField("終了日(YYYY-MM-DD)", validators=[Optional()])
    submit = SubmitField("表示")
