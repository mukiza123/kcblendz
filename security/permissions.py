"""Centralized permission predicates — single source of truth for access rules."""
from flask import session


def is_authenticated() -> bool:
    return bool(session.get("uid"))


def is_admin() -> bool:
    return session.get("role") == "admin"


def can_view_order(order_row) -> bool:
    """Order owner or any admin can view."""
    if not order_row:
        return False
    if is_admin():
        return True
    return is_authenticated() and order_row["user_id"] == session.get("uid")


def can_edit_product() -> bool:
    return is_admin()


def can_export_users() -> bool:
    return is_admin()
