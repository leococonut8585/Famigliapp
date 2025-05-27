from wtforms import ValidationError
import os

class FileSize:
    """Validator to check uploaded file size."""

    def __init__(self, max_size: int, message: str | None = None) -> None:
        self.max_size = max_size
        if message is None:
            mb = max_size // (1024 * 1024)
            message = f"{mb}MB以下のファイルを指定してください"
        self.message = message

    def __call__(self, form, field) -> None:
        data = field.data
        if not data or not hasattr(data, "stream"):
            return
        pos = data.stream.tell()
        data.stream.seek(0, os.SEEK_END)
        size = data.stream.tell()
        data.stream.seek(pos)
        if size > self.max_size:
            raise ValidationError(self.message)
