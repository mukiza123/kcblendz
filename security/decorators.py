"""Permission decorators used across the Flask blueprints."""
from functools import wraps
from flask import session, redirect, url_for, request, flash, abort


def login_required(view):
    @wraps(view)
    def wrapped(*a, **kw):
        if not session.get("uid"):
            flash("Please sign in to continue.", "error")
            return redirect(url_for("login", next=request.path))
        return view(*a, **kw)
    return wrapped
