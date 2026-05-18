"""
KCBlendz unit tests
===================

Run all:
    python -m unittest tests.py -v

Or pick a class:
    python -m unittest tests.AuthTests -v
    python -m unittest tests.CardValidationTests -v

These tests use Flask's test_client + an isolated test database so they do not
touch your production data. Each test class re-seeds a fresh DB before running.
"""
import os
import sys
import json
import unittest
import tempfile
from pathlib import Path

# Force the app to use a temporary DB before importing it
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["KCB_DB_PATH"] = _tmp.name

# We import after setting the env var so app.py picks up the test DB.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import app as kc                                            # noqa: E402

# Override DB_PATH at module level (app reads at import time, so this rebinds)
kc.DB_PATH = Path(_tmp.name)


def _fresh_db():
    """Re-create and re-seed the test database from scratch."""
    if kc.DB_PATH.exists():
        kc.DB_PATH.unlink()
    kc.init_db()


def _csrf(client, route="/login"):
    """Pull a valid CSRF token after fetching a page that populates the session."""
    client.get(route)
    with client.session_transaction() as s:
        return s.get("_csrf")


def _login(client, email, password):
    """Log in and return the session uid (or None on failure)."""
    tok = _csrf(client, "/login")
    r = client.post("/login", data={"_csrf": tok, "email": email, "password": password},
                    follow_redirects=False)
    with client.session_transaction() as s:
        return s.get("uid"), r.status_code


# ─────────────────────────────────────────────────────────────────────────────
# Card validation — pure functions, no test client needed.
# ─────────────────────────────────────────────────────────────────────────────
class CardValidationTests(unittest.TestCase):
    def test_luhn_accepts_valid_visa(self):
        self.assertTrue(kc.luhn_check("4242424242424242"))

    def test_luhn_accepts_valid_mastercard(self):
        self.assertTrue(kc.luhn_check("5555555555554444"))

    def test_luhn_rejects_invalid_number(self):
        self.assertFalse(kc.luhn_check("1234567812345678"))

    def test_luhn_rejects_short_numbers(self):
        self.assertFalse(kc.luhn_check("1234"))

    def test_brand_detection_visa(self):
        self.assertEqual(kc.detect_card_brand("4242424242424242"), "visa")

    def test_brand_detection_mastercard(self):
        self.assertEqual(kc.detect_card_brand("5555555555554444"), "mastercard")

    def test_brand_detection_amex(self):
        self.assertEqual(kc.detect_card_brand("378282246310005"), "amex")

    def test_brand_detection_unknown(self):
        self.assertEqual(kc.detect_card_brand("9999999999999999"), "card")

