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

    def test_validate_form_passes_with_clean_data(self):
        class _F:
            def get(self, k, d=""): return {
                "card_number": "4242 4242 4242 4242",
                "card_name": "John Doe",
                "card_expiry": "12/30",
                "card_cvv": "123",
            }.get(k, d)
        ok, errs, card = kc.validate_card_form(_F())
        self.assertTrue(ok)
        self.assertEqual(errs, [])
        self.assertEqual(card["brand"], "visa")
        self.assertEqual(card["last4"], "4242")

    def test_validate_form_fails_on_expired_card(self):
        class _F:
            def get(self, k, d=""): return {
                "card_number": "4242 4242 4242 4242",
                "card_name": "John",
                "card_expiry": "01/20",  # expired
                "card_cvv": "123",
            }.get(k, d)
        ok, errs, _ = kc.validate_card_form(_F())
        self.assertFalse(ok)
        self.assertTrue(any("expired" in e.lower() for e in errs))

    def test_validate_form_fails_on_short_cvv(self):
        class _F:
            def get(self, k, d=""): return {
                "card_number": "4242 4242 4242 4242",
                "card_name": "John",
                "card_expiry": "12/30",
                "card_cvv": "12",  # too short
            }.get(k, d)
        ok, errs, _ = kc.validate_card_form(_F())
        self.assertFalse(ok)
        self.assertTrue(any("CVV" in e for e in errs))


# ─────────────────────────────────────────────────────────────────────────────
# Public route smoke tests
# ─────────────────────────────────────────────────────────────────────────────
class PublicRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _fresh_db()

    def setUp(self):
        self.client = kc.app.test_client()
        with self.client.session_transaction() as s:
            s["region"] = "MU"

    def test_homepage_returns_200(self):
        r = self.client.get("/home")
        self.assertEqual(r.status_code, 200)

    def test_shop_returns_200(self):
        r = self.client.get("/shop")
        self.assertEqual(r.status_code, 200)

    def test_builder_returns_200(self):
        r = self.client.get("/builder")
        self.assertEqual(r.status_code, 200)

    def test_wellness_returns_200(self):
        r = self.client.get("/wellness")
        self.assertEqual(r.status_code, 200)

    def test_all_static_pages_render(self):
        for path in ("/about", "/contact", "/faq", "/privacy", "/terms",
                     "/refund-policy", "/shipping-policy"):
            with self.subTest(path=path):
                r = self.client.get(path)
                self.assertEqual(r.status_code, 200, f"{path} -> {r.status_code}")

    def test_root_redirects_when_region_set(self):
        r = self.client.get("/", follow_redirects=False)
        self.assertEqual(r.status_code, 302)
        self.assertIn("/home", r.headers["Location"])

    def test_root_redirects_to_store_picker_without_region(self):
        client = kc.app.test_client()  # fresh, no region
        r = client.get("/", follow_redirects=False)
        self.assertEqual(r.status_code, 302)
        self.assertIn("/store", r.headers["Location"])

    def test_sitemap_and_robots_render(self):
        for path in ("/sitemap.xml", "/robots.txt"):
            with self.subTest(path=path):
                r = self.client.get(path)
                self.assertEqual(r.status_code, 200)


# ─────────────────────────────────────────────────────────────────────────────
# Authentication tests — signup bug regression + login flows
# ─────────────────────────────────────────────────────────────────────────────
class AuthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _fresh_db()

    def setUp(self):
        self.client = kc.app.test_client()
        with self.client.session_transaction() as s:
            s["region"] = "MU"

    def test_register_with_single_password_succeeds(self):
        """Regression: previously this said 'passwords don't match' incorrectly."""
        tok = _csrf(self.client, "/register")
        r = self.client.post("/register", data={
            "_csrf": tok, "full_name": "Single Pw", "email": "single@kc.com",
            "phone": "+23055551111", "password": "aaaaaaaa",
        }, follow_redirects=False)
        self.assertEqual(r.status_code, 302)
        self.assertIn("/account", r.headers["Location"])

    def test_register_with_matching_confirm_succeeds(self):
        tok = _csrf(self.client, "/register")
        r = self.client.post("/register", data={
            "_csrf": tok, "full_name": "Match", "email": "match@kc.com",
            "phone": "+23055552222", "password": "bbbbbbbb", "confirm": "bbbbbbbb",
        }, follow_redirects=False)
        self.assertEqual(r.status_code, 302)

    def test_register_with_mismatched_confirm_fails(self):
        tok = _csrf(self.client, "/register")
        r = self.client.post("/register", data={
            "_csrf": tok, "full_name": "Bad", "email": "bad@kc.com",
            "phone": "+23055553333", "password": "cccccccc", "confirm": "different",
        }, follow_redirects=True)
        self.assertIn("do not match", r.get_data(as_text=True))

    def test_register_rejects_short_password(self):
        tok = _csrf(self.client, "/register")
        r = self.client.post("/register", data={
            "_csrf": tok, "full_name": "Short", "email": "short@kc.com",
            "phone": "+23055554444", "password": "abc",
        }, follow_redirects=True)
        self.assertIn("at least 8 characters", r.get_data(as_text=True))

    def test_register_rejects_duplicate_email(self):
        tok = _csrf(self.client, "/register")
        self.client.post("/register", data={
            "_csrf": tok, "full_name": "Dup1", "email": "dup@kc.com",
            "phone": "+23055555555", "password": "aaaaaaaa",
        })
        tok = _csrf(self.client, "/register")
        r = self.client.post("/register", data={
            "_csrf": tok, "full_name": "Dup2", "email": "dup@kc.com",
            "phone": "+23055556666", "password": "aaaaaaaa",
        }, follow_redirects=True)
        self.assertIn("already registered", r.get_data(as_text=True))

    def test_admin_login_uses_2026_password(self):
        uid, status = _login(self.client, "admin@kcblendz.com", "KCBlendz@2026")
        self.assertEqual(status, 302)
        self.assertIsNotNone(uid)

    def test_admin_login_rejects_old_password(self):
        uid, status = _login(self.client, "admin@kcblendz.com", "KCBlendz@2025")
        self.assertEqual(status, 200)            # re-renders form
        self.assertIsNone(uid)


# ─────────────────────────────────────────────────────────────────────────────
# Authorization tests — role-based access control
# ─────────────────────────────────────────────────────────────────────────────
class AuthorizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _fresh_db()

    def setUp(self):
        self.client = kc.app.test_client()
        with self.client.session_transaction() as s:
            s["region"] = "MU"

    def test_guest_cannot_access_account_pages(self):
        for path in ("/account", "/account/orders", "/account/favorites",
                     "/account/profile"):
            with self.subTest(path=path):
                r = self.client.get(path, follow_redirects=False)
                self.assertEqual(r.status_code, 302)
                self.assertIn("/login", r.headers["Location"])

    def test_guest_cannot_access_admin(self):
        r = self.client.get("/admin", follow_redirects=False)
        # admin_required either redirects to /login (302) or forbids outright (403)
        self.assertIn(r.status_code, (302, 403))

    def test_customer_cannot_access_admin(self):
        # Create a regular customer
        tok = _csrf(self.client, "/register")
        self.client.post("/register", data={
            "_csrf": tok, "full_name": "Reg", "email": "reg@kc.com",
            "phone": "+23055557777", "password": "aaaaaaaa",
        })
        # Already logged in as customer now
        r = self.client.get("/admin", follow_redirects=False)
        # Admin decorator should redirect/forbid
        self.assertIn(r.status_code, (302, 403))

    def test_admin_can_access_all_admin_pages(self):
        _login(self.client, "admin@kcblendz.com", "KCBlendz@2026")
        for path in ("/admin", "/admin/products", "/admin/orders", "/admin/users",
                     "/admin/reports", "/admin/blogs", "/admin/builder",
                     "/admin/categories", "/admin/messages", "/admin/notifications"):
            with self.subTest(path=path):
                r = self.client.get(path)
                self.assertEqual(r.status_code, 200, f"{path} -> {r.status_code}")


# ─────────────────────────────────────────────────────────────────────────────
# Favorites + Reviews
