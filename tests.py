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




class LoginTests(_BaseDB):
    def test_admin_login_succeeds(self):
        uid, status = _login(self.client, "admin@kcblendz.com", "Admin1234")
        self.assertIsNotNone(uid)

    def test_login_fails_for_unknown_email(self):
        uid, status = _login(self.client, "ghost@nowhere.com", "x")
        self.assertIsNone(uid)

    def test_login_fails_for_wrong_password(self):
        uid, status = _login(self.client, "admin@kcblendz.com", "WrongPass")
        self.assertIsNone(uid)




class LogoutTests(_BaseDB):
    def test_logout_clears_session(self):
        _login(self.client, "admin@kcblendz.com", "Admin1234")
        tok = _csrf(self.client, "/")
        r = self.client.post("/logout", data={"_csrf": tok}, follow_redirects=False)
        self.assertIn(r.status_code, (200, 302))
        with self.client.session_transaction() as ses:
            self.assertIsNone(ses.get("uid"))

    def test_account_requires_login(self):
        r = self.client.get("/account", follow_redirects=False)
        # should redirect to login
        self.assertIn(r.status_code, (302, 401))




class PasswordHashingTests(unittest.TestCase):
    def test_hash_then_verify_roundtrip(self):
        from security.passwords import hash_password, verify_password
        h = hash_password("Sup3rSecret!")
        self.assertTrue(verify_password("Sup3rSecret!", h))

    def test_wrong_password_rejected(self):
        from security.passwords import hash_password, verify_password
        h = hash_password("Sup3rSecret!")
        self.assertFalse(verify_password("nope", h))

    def test_short_password_rejected(self):
        from security.passwords import hash_password
        with self.assertRaises(ValueError):
            hash_password("123")




class CSRFTests(_BaseDB):
    def test_post_without_token_is_rejected(self):
        r = self.client.post("/login",
                             data={"email": "admin@kcblendz.com", "password": "Admin1234"},
                             follow_redirects=False)
        self.assertEqual(r.status_code, 400)

    def test_post_with_valid_token_passes_csrf(self):
        tok = _csrf(self.client, "/login")
        r = self.client.post("/login",
                             data={"_csrf": tok, "email": "admin@kcblendz.com", "password": "Admin1234"},
                             follow_redirects=False)
        self.assertNotEqual(r.status_code, 400)




class AdminAccessTests(_BaseDB):
    def test_admin_redirects_anon(self):
        r = self.client.get("/admin", follow_redirects=False)
        self.assertIn(r.status_code, (302, 403))

    def test_admin_blocks_non_admin(self):
        # Register a normal user
        tok = _csrf(self.client, "/register")
        self.client.post("/register", data={
            "_csrf": tok, "email": "user@example.com", "full_name": "Reg User",
            "phone": "", "password": "Passw0rd!"
        }, follow_redirects=False)
        _login(self.client, "user@example.com", "Passw0rd!")
        r = self.client.get("/admin", follow_redirects=False)
        self.assertEqual(r.status_code, 403)

    def test_admin_allows_admin(self):
        _login(self.client, "admin@kcblendz.com", "Admin1234")
        r = self.client.get("/admin", follow_redirects=False)
        self.assertEqual(r.status_code, 200)




class UploadValidationTests(unittest.TestCase):
    def test_allowed_file_accepts_image(self):
        from security.uploads import allowed_file
        self.assertTrue(allowed_file("smoothie.png"))
        self.assertTrue(allowed_file("PHOTO.JPG"))

    def test_allowed_file_rejects_script(self):
        from security.uploads import allowed_file
        self.assertFalse(allowed_file("evil.exe"))
        self.assertFalse(allowed_file("payload.php"))
        self.assertFalse(allowed_file(""))

    def test_safe_save_path_blocks_traversal(self):
        from security.uploads import safe_save_path
        import tempfile
        d = tempfile.mkdtemp()
        with self.assertRaises(ValueError):
            safe_save_path(d, "../../etc/passwd")
        with self.assertRaises(ValueError):
            safe_save_path(d, "/abs/path.png")




class CartAddTests(_BaseDB):
    def _seed_product(self):
        with kc.app.app_context():
            db = kc.get_db()
            db.execute(
                "INSERT INTO products (slug, name, price_mur, is_active) VALUES (?, ?, ?, 1)",
                ("tropical-burst", "Tropical Burst", 200.0)
            )
            db.commit()
            return db.execute("SELECT id FROM products WHERE slug = 'tropical-burst'").fetchone()["id"]

    def test_add_to_cart_inserts_line(self):
        pid = self._seed_product()
        tok = _csrf(self.client, "/")
        r = self.client.post("/cart/add",
                             data={"_csrf": tok, "product_id": str(pid), "qty": "2"},
                             follow_redirects=False)
        with self.client.session_transaction() as ses:
            cart = ses.get("cart", [])
        self.assertEqual(len(cart), 1)
        self.assertEqual(cart[0]["qty"], 2)




class CartUpdateRemoveTests(_BaseDB):
    def _seed_and_add(self):
        with kc.app.app_context():
            db = kc.get_db()
            db.execute(
                "INSERT INTO products (slug, name, price_mur, is_active) VALUES (?, ?, ?, 1)",
                ("test-blend", "Test Blend", 100.0)
            )
            db.commit()
            pid = db.execute("SELECT id FROM products WHERE slug='test-blend'").fetchone()["id"]
        tok = _csrf(self.client, "/")
        self.client.post("/cart/add", data={"_csrf": tok, "product_id": str(pid), "qty": "1"},
                         follow_redirects=False)
        with self.client.session_transaction() as ses:
            return ses.get("cart", [])[0]["key"]

    def test_cart_update_changes_qty(self):
        key = self._seed_and_add()
        tok = _csrf(self.client, "/")
        self.client.post("/cart/update", data={"_csrf": tok, "key": key, "qty": "5"},
                         follow_redirects=False)
        with self.client.session_transaction() as ses:
            cart = ses.get("cart", [])
        self.assertEqual(cart[0]["qty"], 5)

    def test_cart_remove_drops_line(self):
        key = self._seed_and_add()
        tok = _csrf(self.client, "/")
        self.client.post("/cart/remove", data={"_csrf": tok, "key": key}, follow_redirects=False)
        with self.client.session_transaction() as ses:
            cart = ses.get("cart", [])
        self.assertEqual(cart, [])




class CartSubtotalTests(_BaseDB):
    def test_subtotal_reflects_multiple_items(self):
        with kc.app.app_context():
            db = kc.get_db()
            db.execute("INSERT INTO products (slug,name,price_mur,is_active) VALUES (?,?,?,1)",
                       ("a", "A", 100.0))
            db.execute("INSERT INTO products (slug,name,price_mur,is_active) VALUES (?,?,?,1)",
                       ("b", "B", 50.0))
            db.commit()
            pa = db.execute("SELECT id FROM products WHERE slug='a'").fetchone()["id"]
            pb = db.execute("SELECT id FROM products WHERE slug='b'").fetchone()["id"]
        tok = _csrf(self.client, "/")
        self.client.post("/cart/add", data={"_csrf": tok, "product_id": str(pa), "qty": "2"})
        tok = _csrf(self.client, "/")
        self.client.post("/cart/add", data={"_csrf": tok, "product_id": str(pb), "qty": "3"})
        r = self.client.get("/cart")
        # 2*100 + 3*50 = 350
        self.assertIn(b"350", r.data)




class CheckoutFlowTests(_BaseDB):
    def test_empty_cart_redirects_to_cart(self):
        r = self.client.get("/checkout", follow_redirects=False)
        self.assertEqual(r.status_code, 302)
        self.assertIn("/cart", r.headers["Location"])

    def test_checkout_renders_with_items(self):
        with kc.app.app_context():
            db = kc.get_db()
            db.execute("INSERT INTO products (slug,name,price_mur,is_active) VALUES (?,?,?,1)",
                       ("co", "CO Smoothie", 250.0))
            db.commit()
            pid = db.execute("SELECT id FROM products WHERE slug='co'").fetchone()["id"]
        tok = _csrf(self.client, "/")
        self.client.post("/cart/add", data={"_csrf": tok, "product_id": str(pid), "qty": "1"})
        r = self.client.get("/checkout")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"Checkout", r.data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
