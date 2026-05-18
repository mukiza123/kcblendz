"""Append-only audit log helper."""
import json
from flask import request, session


def audit(db, action: str, entity: str = None, entity_id: int = None, meta: dict = None) -> None:
    """Record an admin / sensitive action. db is a sqlite3 connection."""
    meta_json = json.dumps(meta) if meta else None
    ip = request.headers.get("X-Forwarded-For", request.remote_addr) if request else None
    db.execute(
        """INSERT INTO audit_log (actor_user_id, action, entity, entity_id, meta, ip)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (session.get("uid") if session else None, action, entity, entity_id, meta_json, ip)
    )
    db.commit()
