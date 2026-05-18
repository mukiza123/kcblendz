"""Input validators — keep them small, pure, and fast."""
import re

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"^\+?[0-9\s\-\(\)]{7,20}$")


def valid_email(s: str) -> bool:
    return bool(s and EMAIL_RE.match(s.strip()))


def valid_phone(s: str) -> bool:
    if not s:
        return False
    digits = re.sub(r"[^0-9]", "", s)
    return 7 <= len(digits) <= 15 and bool(PHONE_RE.match(s.strip()))


def valid_name(s: str) -> bool:
    return bool(s and 2 <= len(s.strip()) <= 80)


def valid_password_strength(s: str) -> bool:
    return bool(s and len(s) >= 8 and re.search(r"[A-Za-z]", s) and re.search(r"\d", s))
