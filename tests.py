"""
KCBlendz unit tests
===================

Run all:
    py -m unittest tests.py -v

These tests use Flask's test_client + an isolated test database so they do not
touch production data.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Force the app to use a temporary DB before importing it
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["KCB_DB_PATH"] = _tmp.name

sys.path.insert(0, str(Path(__file__).resolve().parent))
import app as kc  # noqa: E402




def _fresh_db():
    """Re-create and re-seed the test database from scratch."""
    if kc.DB_PATH.exists():
        kc.DB_PATH.unlink()
    # init_db will be added later; tolerate missing for now
    if hasattr(kc, "init_db"):
        with kc.app.app_context():
            kc.init_db()




def _csrf(client, route="/login"):
    """Pull a valid CSRF token after fetching a page that populates the session."""
    client.get(route, follow_redirects=True)
    with client.session_transaction() as ses:
        return ses.get("_csrf")




def _login(client, email, password):
    """Log in and return the session uid (or None on failure)."""
    tok = _csrf(client, "/login")
    r = client.post(
        "/login",
        data={"_csrf": tok, "email": email, "password": password},
        follow_redirects=False,
    )
    with client.session_transaction() as ses:
        return ses.get("uid"), r.status_code


class _BaseDB(unittest.TestCase):
    def setUp(self):
        _fresh_db()
        # Reset any module-level rate-limit state from previous tests so
        # repeated login()s don't trip the limiter across cases.
        try:
            from security import ratelimit as _rl
            with _rl._lock:
                _rl._buckets.clear()
        except Exception:
            pass
        self.client = kc.app.test_client()

    def tearDown(self):
        if kc.DB_PATH.exists():
            kc.DB_PATH.unlink()


class SmokeTests(unittest.TestCase):
    def test_root_responds(self):
        with kc.app.test_client() as c:
            r = c.get("/")
            self.assertIn(r.status_code, (200, 302))


if __name__ == "__main__":
    unittest.main(verbosity=2)
