"""Input sanitization helpers — strip HTML/control chars, clamp lengths."""
import re
from markupsafe import escape


_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean_text(s, max_len: int = 500) -> str:
    if not s:
        return ""
    s = _CONTROL_RE.sub("", str(s))
    s = s.strip()
    return s[:max_len]


def safe_html_inline(s) -> str:
    """Escape HTML entirely — use for any text rendered from user input."""
    return str(escape(s or ""))


def sanitize_slug(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:80]
