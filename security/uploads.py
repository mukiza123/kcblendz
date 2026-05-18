"""Upload helpers — file-type and filename safety."""
import os
from werkzeug.utils import secure_filename

ALLOWED_IMAGE_EXT = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_UPLOAD_MB = 8


def allowed_file(filename: str) -> bool:
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_IMAGE_EXT


def safe_save_path(upload_dir: str, filename: str) -> str:
    name = secure_filename(filename)
    if not name:
        raise ValueError("Unsafe filename.")
    return os.path.join(upload_dir, name)
