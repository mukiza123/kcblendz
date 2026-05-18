"""Synchronizer-token CSRF helpers."""
import secrets
from flask import session


def csrf_token() -> str:
    tok = session.get("_csrf")
    if not tok:
        tok = secrets.token_urlsafe(32)
        session["_csrf"] = tok
    return tok


def check_csrf(submitted: str) -> bool:
    expected = session.get("_csrf")
    return bool(expected and submitted and secrets.compare_digest(expected, submitted))
