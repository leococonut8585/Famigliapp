"""Forms for Calendario blueprint."""

from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    DateField,
    # TimeField, # Removed TimeField as it's being replaced by SelectField for time
    TextAreaField,
    SubmitField,
    SelectField,
    SelectMultipleField,
    widgets # widgets をインポート
)
from wtforms.validators import DataRequired, Optional
import config

# Define time_choices for SelectFields
time_choices = [(f"{h:02d}:{m:02d}", f"{h:02d}:{m:02d}") for h in range(24) for m in [0, 15, 30, 45]]

class EventForm(FlaskForm):
    """Form to create or edit an event."""

    date = DateField("日付", validators=[DataRequired()])
    title = StringField("タイトル", validators=[DataRequired()])
    description = TextAreaField("内容", validators=[Optional()])
    category = SelectField(
        "種類",
        choices=[
            ("shift", "シフト"),
            ("lesson", "レッスン"),
            ("hug", "ハグの日"),
            ('kouza', '講座'),
            ('mummy', 'マミー系'),
            ('tattoo', 'タトゥー'),
            ('shucchou', '出張'),
            ("other", "その他"),
        ],
        validators=[DataRequired()],
        # カテゴリ変更時にJavaScriptで対象者の表示/非表示を切り替えるための属性を追加
        render_kw={'onchange': 'toggleParticipantsField(this.value); toggleTimeField(this.value);'}
    )
    start_time = SelectField(
        '開始時間',
        choices=time_choices,
        validators=[Optional()],
        render_kw={'class': 'time-select', 'id': 'event_start_time'}
    )
    end_time = SelectField(
        '終了時間',
        choices=time_choices,
        validators=[Optional()],
        render_kw={'class': 'time-select', 'id': 'event_end_time'}
    )
    participants = SelectMultipleField(
        "対象者",
        choices=[(u, u) for u in config.USERS if u not in config.EXCLUDED_USERS],
        validators=[Optional()],
        widget=widgets.ListWidget(prefix_label=False), # チェックボックスリスト表示用ウィジェット
        option_widget=widgets.CheckboxInput() # 個々の選択肢をチェックボックスとして表示
    )
    submit = SubmitField("保存")
    delete = SubmitField("この予定を削除する", render_kw={'class': 'btn btn-danger'})


class StatsForm(FlaskForm):
    """Form to filter statistics by date range."""

    start = DateField("開始日", validators=[Optional()])
    end = DateField("終了日", validators=[Optional()])
    submit = SubmitField("表示")


class ShiftRulesForm(FlaskForm):
    """Form to edit shift calculation rules."""

    max_consecutive_days = StringField("連勤最大日数", validators=[Optional()])
    min_staff_per_day = StringField("最低人数", validators=[Optional()])
    forbidden_pairs = StringField("禁止組み合わせ", validators=[Optional()])
    required_pairs = StringField("必須組み合わせ", validators=[Optional()])
    employee_attributes = StringField("従業員属性", validators=[Optional()])
    required_attributes = StringField("属性ごとの必要人数", validators=[Optional()])

    # 新しく追加するフィールド
    specialized_requirements_json_str = StringField("専門予定JSON", validators=[Optional()])

    submit = SubmitField("保存")


class ShiftManagementForm(FlaskForm):
    """Minimal form for CSRF token generation on the shift management page."""
    # No fields needed other than what FlaskForm provides (e.g., CSRF token)
    # If we needed a submit button tied to this specific form for some reason:
    # submit_shifts = SubmitField('更新') # Example, not strictly needed if using JS/other buttons
    pass
