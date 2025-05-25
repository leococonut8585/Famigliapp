"""Forms for Punto blueprint."""

from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField
from wtforms.validators import DataRequired


class EditPointsForm(FlaskForm):
    """Form to edit a user's points."""

    a = IntegerField("Aポイント", validators=[DataRequired()])
    o = IntegerField("Oポイント", validators=[DataRequired()])
    u = IntegerField("Uポイント", render_kw={"readonly": True})
    submit = SubmitField("保存")
