from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField, SelectField
from wtforms.validators import DataRequired


class AddBravissimoForm(FlaskForm):
    target = SelectField("対象ユーザー", validators=[DataRequired()], choices=[])
    audio = FileField("音声ファイル", validators=[DataRequired()])
    submit = SubmitField("投稿")



class BravissimoFilterForm(FlaskForm):
    author = StringField("投稿者")
    target = StringField("対象ユーザー")
    keyword = StringField("検索語")
    submit = SubmitField("絞り込み")
