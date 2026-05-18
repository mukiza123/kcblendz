"""Permission decorators used across the Flask blueprints."""
from functools import wraps
from flask import session, redirect, url_for, request, flash, abort
from security.permissions import is_authenticated, is_admin


def login_required(view):
    @wraps(view)
    def wrapped(*a, **kw):
        if not is_authenticated():
            flash("Please sign in to continue.", "error")
            return redirect(url_for("login", next=request.path))
        return view(*a, **kw)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*a, **kw):
        if not is_admin():
            abort(403)
        return view(*a, **kw)
    return wrapped


def region_required(view):
    @wraps(view)
    def wrapped(*a, **kw):
        if not session.get("region"):
            return redirect(url_for("store_select"))
        return view(*a, **kw)
    return wrapped
