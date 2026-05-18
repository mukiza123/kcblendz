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


class CardValidationTests(unittest.TestCase):
    def test_luhn_accepts_valid_visa(self):
        self.assertTrue(kc.luhn_check("4242424242424242"))

    def test_luhn_accepts_valid_mastercard(self):
        self.assertTrue(kc.luhn_check("5555555555554444"))

    def test_luhn_rejects_invalid_number(self):
        self.assertFalse(kc.luhn_check("1234567812345678"))

    def test_luhn_rejects_short_numbers(self):
        self.assertFalse(kc.luhn_check("1234"))

    def test_luhn_rejects_empty(self):
        self.assertFalse(kc.luhn_check(""))




class CardBrandTests(unittest.TestCase):
    def test_brand_detection_visa(self):
        self.assertEqual(kc.detect_card_brand("4242424242424242"), "visa")

    def test_brand_detection_mastercard(self):
        self.assertEqual(kc.detect_card_brand("5555555555554444"), "mastercard")

    def test_brand_detection_amex(self):
        self.assertEqual(kc.detect_card_brand("378282246310005"), "amex")

    def test_brand_detection_discover(self):
        self.assertEqual(kc.detect_card_brand("6011111111111117"), "discover")

    def test_brand_detection_unknown(self):
        self.assertEqual(kc.detect_card_brand("1234567890"), "unknown")




class CardFormValidationTests(unittest.TestCase):
    def test_form_accepts_valid_payload(self):
        errors = kc.validate_card_form({
            "card_number": "4242 4242 4242 4242",
            "card_name": "Jane Doe",
            "card_exp": "08/28",
            "card_cvc": "123",
        })
        self.assertEqual(errors, [])

    def test_form_rejects_bad_expiry(self):
        errors = kc.validate_card_form({
            "card_number": "4242424242424242",
            "card_name": "Jane Doe",
            "card_exp": "13/28",
            "card_cvc": "123",
        })
        self.assertTrue(any("Expiry" in e for e in errors))

    def test_form_rejects_short_cvc(self):
        errors = kc.validate_card_form({
            "card_number": "4242424242424242",
            "card_name": "Jane Doe",
            "card_exp": "08/28",
            "card_cvc": "1",
        })
        self.assertTrue(any("CVC" in e for e in errors))




class RegistrationTests(_BaseDB):
    def test_register_creates_user(self):
        tok = _csrf(self.client, "/register")
        r = self.client.post("/register", data={
            "_csrf": tok, "email": "new@example.com", "full_name": "New User",
            "phone": "+23012345678", "password": "Passw0rd!"
        }, follow_redirects=False)
        self.assertIn(r.status_code, (200, 302))
        with kc.app.app_context():
            row = kc.get_db().execute(
                "SELECT email FROM users WHERE email = ?", ("new@example.com",)
            ).fetchone()
            self.assertIsNotNone(row)

    def test_register_rejects_bad_email(self):
        tok = _csrf(self.client, "/register")
        r = self.client.post("/register", data={
            "_csrf": tok, "email": "not-an-email", "full_name": "X",
            "phone": "", "password": "Passw0rd!"
        }, follow_redirects=False)
        self.assertEqual(r.status_code, 200)

    def test_register_rejects_weak_password(self):
        tok = _csrf(self.client, "/register")
        r = self.client.post("/register", data={
            "_csrf": tok, "email": "x@y.com", "full_name": "X",
            "phone": "", "password": "123"
        }, follow_redirects=False)
        self.assertEqual(r.status_code, 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
