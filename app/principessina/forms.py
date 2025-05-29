"""Forms for Decima (formerly Principessina) blueprint."""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import StringField, TextAreaField, SubmitField, FileField, SelectField # Added SelectField
from wtforms.validators import DataRequired, Optional, Length

from app.validators import FileSize
from . import utils 


class ReportForm(FlaskForm):
    """Form to add a Decima text report (Yura or Mangiato)."""
    text_content = TextAreaField("報告内容", validators=[DataRequired()])
    submit = SubmitField("報告する")


class VideoUploadForm(FlaskForm):
    """Form to upload a video."""
    title = StringField("タイトル（任意）", validators=[Optional(), Length(max=200)])
    video_file = FileField(
        "動画ファイル", 
        validators=[
            DataRequired(message="動画ファイルを選択してください。"), 
            FileAllowed(utils.ALLOWED_VIDEO_EXTS, "許可されていない動画形式です。"), 
            FileSize(utils.MAX_MEDIA_SIZE)
        ]
    )
    submit = SubmitField("アップロード")


class PhotoUploadForm(FlaskForm):
    """Form to upload a photo."""
    title = StringField("タイトル（任意）", validators=[Optional(), Length(max=200)])
    photo_file = FileField(
        "写真ファイル", 
        validators=[
            DataRequired(message="写真ファイルを選択してください。"), 
            FileAllowed(utils.ALLOWED_PHOTO_EXTS, "許可されていない写真形式です。"), 
            FileSize(utils.MAX_MEDIA_SIZE)
        ]
    )
    submit = SubmitField("アップロード")


class CreateCustomFolderForm(FlaskForm):
    """Form to create a new custom folder for media."""
    folder_name = StringField(
        "新しいフォルダ名", 
        validators=[
            DataRequired(message="フォルダ名を入力してください。"), 
            Length(min=1, max=100, message="フォルダ名は1文字以上100文字以内で入力してください。")
        ]
    )
    submit = SubmitField("フォルダ作成")


class CopyMediaToCustomFolderForm(FlaskForm):
    """Form to copy (reference) a media item to a custom folder."""
    target_custom_folder = SelectField(
        "コピー先のカスタムフォルダ", 
        choices=[], # To be populated dynamically in the route
        validators=[DataRequired(message="コピー先のフォルダを選択してください。")]
    )
    submit_copy = SubmitField("このフォルダにコピー")
