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
    if not filename:
        raise ValueError("Unsafe filename.")
    # Reject obvious traversal attempts before secure_filename strips them
    if ".." in filename or filename.startswith(("/", "\\")):
        raise ValueError("Filename contains illegal path components.")
    name = secure_filename(filename)
    if not name:
        raise ValueError("Unsafe filename.")
    # Final guard: resolved path must remain inside upload_dir
    full = os.path.abspath(os.path.join(upload_dir, name))
    if not full.startswith(os.path.abspath(upload_dir) + os.sep):
        raise ValueError("Path escapes upload directory.")
    return full


def sanitize_filename(name: str) -> str:
    """Return a safe disk filename, stripping path traversal characters."""
    if not name:
        return ""
    clean = secure_filename(name)
    # Disallow leading dots (hidden files) and empty results
    clean = clean.lstrip(".")
    return clean or "upload"


def reject_path_traversal(name: str) -> None:
    if name and (".." in name or "/" in name or "\\" in name or name.startswith(("/", "\\"))):
        raise ValueError("Filename contains illegal path components.")
