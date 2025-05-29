"""Forms for Decima (formerly Principessina) blueprint."""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed # Re-added
from wtforms import StringField, TextAreaField, SubmitField, FileField # Re-added FileField, StringField
from wtforms.validators import DataRequired, Optional, Length # Re-added Optional, added Length

from app.validators import FileSize # Re-added
from . import utils # Added for accessing constants


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
            # Consider adding a Regexp validator here for allowed characters in folder names
            # e.g., Regexp(r'^[a-zA-Z0-9_-]+$', message="フォルダ名には英数字、アンダースコア、ハイフンのみ使用できます。")
        ]
    )
    submit = SubmitField("フォルダ作成")
