"""
KCBlendz — Premium Smoothie & Wellness E-commerce Platform.

Monolithic Flask application backed by SQLite.
"""
import os
import secrets
from datetime import timedelta
from pathlib import Path

from flask import Flask

# ─── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "kcblendz.db"
UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
ALLOWED_IMAGE_EXT = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_UPLOAD_MB = 8

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("KCB_SECRET", secrets.token_hex(32)),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("KCB_FORCE_SECURE", "") == "1",
    SESSION_COOKIE_NAME="kcb_sess",
    PERMANENT_SESSION_LIFETIME=timedelta(days=30),
    MAX_CONTENT_LENGTH=MAX_UPLOAD_MB * 1024 * 1024,
    UPLOAD_FOLDER=str(UPLOAD_FOLDER),
)
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)





# ─── Schema ─────────────────────────────────────────────────────────────────
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    phone TEXT,
    role TEXT NOT NULL DEFAULT 'customer',
    status TEXT NOT NULL DEFAULT 'active',
    region TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_login_at TEXT
);
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    icon TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    short_description TEXT,
    description TEXT,
    ingredients TEXT,
    health_benefits TEXT,
    category_id INTEGER REFERENCES categories(id),
    image_url TEXT,
    price_ngn REAL,
    price_mur REAL,
    price_usd REAL,
    stock INTEGER NOT NULL DEFAULT 100,
    is_available_ng INTEGER NOT NULL DEFAULT 1,
    is_available_mu INTEGER NOT NULL DEFAULT 1,
    is_available_global INTEGER NOT NULL DEFAULT 0,
    is_featured INTEGER NOT NULL DEFAULT 0,
    is_bestseller INTEGER NOT NULL DEFAULT 0,
    is_new INTEGER NOT NULL DEFAULT 0,
    tags TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    is_active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    guest_email TEXT,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT NOT NULL,
    region TEXT NOT NULL,
    currency TEXT NOT NULL,
    subtotal REAL NOT NULL,
    delivery_fee REAL NOT NULL DEFAULT 0,
    total REAL NOT NULL,
    payment_method TEXT,
    payment_status TEXT NOT NULL DEFAULT 'pending',
    order_status TEXT NOT NULL DEFAULT 'pending',
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES products(id) ON DELETE SET NULL,
    smoothie_id INTEGER,
    item_type TEXT NOT NULL DEFAULT 'product',
    name_snapshot TEXT NOT NULL,
    unit_price REAL NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    line_total REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS addresses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    label TEXT,
    full_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    street TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT,
    country TEXT NOT NULL,
    postal_code TEXT,
    is_default INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(user_id, product_id)
);


CREATE TABLE IF NOT EXISTS builder_options (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    option_type TEXT NOT NULL,
    name TEXT NOT NULL,
    price_ngn REAL NOT NULL DEFAULT 0,
    price_mur REAL NOT NULL DEFAULT 0,
    price_usd REAL NOT NULL DEFAULT 0,
    image_url TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS custom_smoothies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    config_json TEXT NOT NULL,
    region TEXT NOT NULL,
    price REAL NOT NULL,
    currency TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);


CREATE TABLE IF NOT EXISTS blogs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    excerpt TEXT,
    body TEXT,
    cover_url TEXT,
    is_published INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    body TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    audience TEXT NOT NULL DEFAULT 'user',
    title TEXT NOT NULL,
    body TEXT,
    link TEXT,
    is_read INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    entity TEXT,
    entity_id INTEGER,
    meta TEXT,
    ip TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS newsletter_subs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

# ─── DB ─────────────────────────────────────────────────────────────────────
import sqlite3


def get_db():
    from flask import g
    if "db" not in g:
        g.db = sqlite3.connect(str(DB_PATH))
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_):
    from flask import g
    db = g.pop("db", None)
    if db is not None:
        db.close()




# ─── CSRF middleware ───────────────────────────────────────────────────────
from security.csrf import csrf_token as _gen_csrf, check_csrf as _check_csrf


@app.before_request
def _enforce_csrf():
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        submitted = request.form.get("_csrf") or request.headers.get("X-CSRF-Token")
        if not _check_csrf(submitted or ""):
            abort(400, "CSRF check failed.")


@app.context_processor
def _inject_csrf():
    return {"csrf_token": _gen_csrf}


# ─── Security headers ──────────────────────────────────────────────────────
from security.headers import security_headers as _sec_headers


@app.after_request
def _apply_security_headers(resp):
    return _sec_headers(resp)


@app.before_request
def _check_user_status():
    uid = session.get("uid")
    if uid:
        try:
            row = get_db().execute("SELECT status FROM users WHERE id = ?", (uid,)).fetchone()
            if row and row["status"] != "active":
                session.clear()
        except Exception:
            pass

# ─── DB init / seed ────────────────────────────────────────────────────────
from security.passwords import hash_password


def init_db():
    """Create tables and seed default categories + admin user."""
    db = get_db()
    db.executescript(SCHEMA_SQL)
    # Seed admin
    if not db.execute("SELECT 1 FROM users WHERE role = 'admin'").fetchone():
        db.execute(
            "INSERT INTO users (email, password_hash, full_name, role) VALUES (?, ?, ?, 'admin')",
            ("admin@kcblendz.com", hash_password("Admin1234"), "KCBlendz Admin")
        )
    # Seed categories
    cats = [
        ("smoothies", "Smoothies", "Real-fruit blends", "🥤", 1),
        ("juices", "Juices", "Cold-pressed", "🧃", 2),
        ("wellness", "Wellness", "Boosters & shots", "🌿", 3),
    ]
    for slug, name, desc, icon, order in cats:
        db.execute(
            "INSERT OR IGNORE INTO categories (slug, name, description, icon, sort_order) VALUES (?, ?, ?, ?, ?)",
            (slug, name, desc, icon, order)
        )
    db.commit()


def _ensure_db():
    if not DB_PATH.exists():
        with app.app_context():
            init_db()


@app.cli.command("init-db")
def cli_init_db():
    """Initialize / seed the database (idempotent)."""
    init_db()
    print("Database initialized.")


@app.route("/shop")
def shop():
    db = get_db()
    q = (request.args.get("q") or "").strip()
    cat = request.args.get("category") or ""
    sort = request.args.get("sort", "new")

    sql = ["SELECT p.*, c.slug AS category_slug FROM products p",
           "LEFT JOIN categories c ON c.id = p.category_id",
           "WHERE p.is_active = 1"]
    params = []
    if q:
        sql.append("AND (p.name LIKE ? OR p.tags LIKE ? OR p.description LIKE ?)")
        like = f"%{q}%"
        params += [like, like, like]
    if cat:
        sql.append("AND c.slug = ?")
        params.append(cat)
    sql.append({
        "price-asc": "ORDER BY COALESCE(p.price_mur, p.price_ngn, p.price_usd) ASC",
        "price-desc": "ORDER BY COALESCE(p.price_mur, p.price_ngn, p.price_usd) DESC",
        "new": "ORDER BY p.created_at DESC",
    }.get(sort, "ORDER BY p.created_at DESC"))

    products = db.execute(" ".join(sql), params).fetchall()
    cats = db.execute("SELECT * FROM categories WHERE is_active = 1 ORDER BY sort_order").fetchall()
    return render_template("public/shop.html",
                           products=products, categories=cats, q=q, cat=cat, sort=sort)


@app.route("/product/<slug>")
def product_detail(slug):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE slug = ? AND is_active = 1", (slug,)).fetchone()
    if not product:
        abort(404)
    reviews = db.execute(
        "SELECT r.*, u.full_name FROM reviews r LEFT JOIN users u ON u.id = r.user_id "
        "WHERE r.product_id = ? ORDER BY r.created_at DESC", (product["id"],)
    ).fetchall()
    avg = db.execute(
        "SELECT ROUND(AVG(rating),1) AS avg, COUNT(*) AS n FROM reviews WHERE product_id = ?",
        (product["id"],)
    ).fetchone()
    return render_template("public/product.html", product=product, reviews=reviews, avg=avg)


@app.route("/builder")
def builder():
    db = get_db()
    options = db.execute(
        "SELECT * FROM builder_options WHERE is_active = 1 ORDER BY option_type, sort_order"
    ).fetchall()
    grouped = {}
    for o in options:
        grouped.setdefault(o["option_type"], []).append(dict(o))
    return render_template("public/builder.html", options=grouped)


@app.route("/api/builder/price", methods=["POST"])
def api_builder_price():
    from flask import jsonify
    payload = request.get_json(silent=True) or {}
    selected_ids = []
    for key in ("cup_size", "base", "fruits", "sweeteners", "addons", "boosters"):
        v = payload.get(key)
        if isinstance(v, list):
            selected_ids.extend(int(x) for x in v if str(x).isdigit())
        elif v is not None and str(v).isdigit():
            selected_ids.append(int(v))
    if not selected_ids:
        return jsonify({"price": 0, "currency": session.get("region", "MU")})
    placeholders = ",".join("?" for _ in selected_ids)
    rows = get_db().execute(
        f"SELECT price_mur, price_ngn, price_usd FROM builder_options WHERE id IN ({placeholders})",
        selected_ids
    ).fetchall()
    region = session.get("region", "MU")
    field = {"MU": "price_mur", "NG": "price_ngn", "GL": "price_usd"}[region]
    total = round(sum((r[field] or 0) for r in rows), 2)
    return jsonify({"price": total, "currency": region})



# ─── Payments ──────────────────────────────────────────────────────────────
def luhn_check(card_number: str) -> bool:
    digits = [int(c) for c in (card_number or "") if c.isdigit()]
    if not (12 <= len(digits) <= 19):
        return False
    s, alt = 0, False
    for d in reversed(digits):
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        s += d
        alt = not alt
    return s % 10 == 0


def detect_card_brand(card_number: str) -> str:
    n = "".join(c for c in (card_number or "") if c.isdigit())
    if not n:
        return "unknown"
    if n.startswith("4"):
        return "visa"
    if 51 <= int(n[:2] or 0) <= 55 or 2221 <= int(n[:4] or 0) <= 2720:
        return "mastercard"
    if n[:2] in ("34", "37"):
        return "amex"
    if n.startswith("6011") or n.startswith("65"):
        return "discover"
    return "unknown"


def validate_card_form(form):
    errors = []
    number = (form.get("card_number") or "").replace(" ", "")
    if not luhn_check(number):
        errors.append("Invalid card number.")
    name = (form.get("card_name") or "").strip()
    if not name or len(name) < 2:
        errors.append("Cardholder name required.")
    exp = (form.get("card_exp") or "").strip()
    import re as _re
    if not _re.match(r"^(0[1-9]|1[0-2])/\d{2}$", exp):
        errors.append("Expiry must be MM/YY.")
    cvc = (form.get("card_cvc") or "").strip()
    if not cvc.isdigit() or not (3 <= len(cvc) <= 4):
        errors.append("CVC must be 3 or 4 digits.")
    return errors

# ─── Cart ──────────────────────────────────────────────────────────────────
def _get_cart():
    return session.setdefault("cart", [])


@app.route("/cart")
def cart():
    db = get_db()
    items = []
    subtotal = 0.0
    for ln in _get_cart():
        if ln.get("type") == "product":
            p = db.execute("SELECT * FROM products WHERE id = ?", (ln["product_id"],)).fetchone()
            if not p:
                continue
            price = p["price_mur"] or p["price_ngn"] or p["price_usd"] or 0
            items.append({"name": p["name"], "qty": ln["qty"], "unit": price,
                          "line": price * ln["qty"], "key": ln["key"]})
            subtotal += price * ln["qty"]
        else:
            items.append({"name": ln["name"], "qty": ln["qty"], "unit": ln["price"],
                          "line": ln["price"] * ln["qty"], "key": ln["key"]})
            subtotal += ln["price"] * ln["qty"]
    return render_template("public/cart.html", items=items, subtotal=round(subtotal, 2))


@app.route("/cart/add", methods=["POST"])
def cart_add():
    pid = int(request.form.get("product_id") or 0)
    qty = max(1, int(request.form.get("qty") or 1))
    cart_l = _get_cart()
    for ln in cart_l:
        if ln.get("product_id") == pid:
            ln["qty"] += qty
            session.modified = True
            return redirect(url_for("cart"))
    cart_l.append({"key": secrets.token_hex(8), "type": "product", "product_id": pid, "qty": qty})
    session.modified = True
    return redirect(url_for("cart"))


@app.route("/cart/update", methods=["POST"])
def cart_update():
    key = request.form.get("key")
    qty = max(0, int(request.form.get("qty") or 0))
    session["cart"] = [ln for ln in _get_cart() if ln["key"] != key or qty > 0]
    for ln in session["cart"]:
        if ln["key"] == key:
            ln["qty"] = qty
    session.modified = True
    return redirect(url_for("cart"))


@app.route("/cart/remove", methods=["POST"])
def cart_remove():
    key = request.form.get("key")
    session["cart"] = [ln for ln in _get_cart() if ln["key"] != key]
    session.modified = True
    return redirect(url_for("cart"))


# ─── Checkout ──────────────────────────────────────────────────────────────
def _delivery_fee_for(region):
    return {"MU": 50, "NG": 1500, "GL": 10}.get(region, 0)


@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    if not _get_cart():
        flash("Your cart is empty.", "error")
        return redirect(url_for("cart"))

    db = get_db()
    subtotal = 0.0
    for ln in _get_cart():
        if ln.get("type") == "product":
            p = db.execute("SELECT * FROM products WHERE id = ?", (ln["product_id"],)).fetchone()
            if p:
                price = p["price_mur"] or p["price_ngn"] or p["price_usd"] or 0
                subtotal += price * ln["qty"]
        else:
            subtotal += ln["price"] * ln["qty"]

    region = session.get("region", "MU")
    fee = _delivery_fee_for(region)
    total = round(subtotal + fee, 2)

    if request.method == "POST":
        full_name = (request.form.get("full_name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        phone = (request.form.get("phone") or "").strip()
        if not (full_name and email and phone):
            flash("Please fill in all fields.", "error")
        else:
            import uuid
            order_number = "KCB-" + uuid.uuid4().hex[:10].upper()
            cur = db.execute(
                """INSERT INTO orders (order_number, user_id, guest_email, full_name, email,
                   phone, region, currency, subtotal, delivery_fee, total)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (order_number, session.get("uid"), None if session.get("uid") else email,
                 full_name, email, phone, region, region, subtotal, fee, total)
            )
            order_id = cur.lastrowid
            for ln in _get_cart():
                if ln.get("type") == "product":
                    p = db.execute("SELECT * FROM products WHERE id = ?", (ln["product_id"],)).fetchone()
                    if not p:
                        continue
                    price = p["price_mur"] or p["price_ngn"] or p["price_usd"] or 0
                    db.execute(
                        """INSERT INTO order_items (order_id, product_id, item_type, name_snapshot,
                           unit_price, quantity, line_total) VALUES (?, ?, 'product', ?, ?, ?, ?)""",
                        (order_id, p["id"], p["name"], price, ln["qty"], price * ln["qty"])
                    )
                else:
                    db.execute(
                        """INSERT INTO order_items (order_id, item_type, name_snapshot, unit_price,
                           quantity, line_total) VALUES (?, 'builder', ?, ?, ?, ?)""",
                        (order_id, ln["name"], ln["price"], ln["qty"], ln["price"] * ln["qty"])
                    )
            db.commit()
            return redirect(url_for("payment", order_id=order_id))

    return render_template("public/checkout.html",
                           subtotal=subtotal, fee=fee, total=total, region=region)


@app.route("/payment/<int:order_id>")
def payment(order_id):
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        abort(404)
    return render_template("public/payment.html", order=order)


@app.route("/payment/<int:order_id>/process", methods=["POST"])
def payment_process(order_id):
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        abort(404)
    method = request.form.get("method") or "card"
    if method == "card":
        errs = validate_card_form(request.form)
        if errs:
            for e in errs:
                flash(e, "error")
            return redirect(url_for("payment", order_id=order_id))
    db.execute(
        "UPDATE orders SET payment_method = ?, payment_status = 'paid', order_status = 'confirmed' "
        "WHERE id = ?", (method, order_id)
    )
    db.commit()
    session.pop("cart", None)
    return redirect(url_for("order_thanks", order_id=order_id))


@app.route("/order/<int:order_id>/thanks")
def order_thanks(order_id):
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        abort(404)
    return render_template("public/order_thanks.html", order=order)


# ─── Account ───────────────────────────────────────────────────────────────
from security.decorators import login_required


@app.route("/account")
@login_required
def account_dashboard():
    db = get_db()
    uid = session["uid"]
    user = db.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
    orders = db.execute(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC LIMIT 5", (uid,)
    ).fetchall()
    return render_template("account/dashboard.html", user=user, orders=orders)


@app.route("/account/orders")
@login_required
def account_orders():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC", (session["uid"],)
    ).fetchall()
    return render_template("account/orders.html", orders=rows)


@app.route("/account/orders/<int:order_id>")
@login_required
def account_order_detail(order_id):
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id = ? AND user_id = ?",
                       (order_id, session["uid"])).fetchone()
    if not order:
        abort(404)
    items = db.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
    return render_template("account/order_detail.html", order=order, items=items)


@app.route("/account/saved-smoothies")
@login_required
def account_saved():
    db = get_db()
    rows = db.execute(
        "SELECT * FROM custom_smoothies WHERE user_id = ? ORDER BY created_at DESC",
        (session["uid"],)
    ).fetchall()
    return render_template("account/saved_smoothies.html", smoothies=rows)


@app.route("/account/addresses", methods=["GET", "POST"])
@login_required
def account_addresses():
    db = get_db()
    if request.method == "POST":
        db.execute(
            """INSERT INTO addresses (user_id, label, full_name, phone, street, city,
               state, country, postal_code) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (session["uid"], request.form.get("label"), request.form.get("full_name"),
             request.form.get("phone"), request.form.get("street"), request.form.get("city"),
             request.form.get("state"), request.form.get("country") or "Mauritius",
             request.form.get("postal_code"))
        )
        db.commit()
        flash("Address saved.", "success")
        return redirect(url_for("account_addresses"))
    rows = db.execute(
        "SELECT * FROM addresses WHERE user_id = ? ORDER BY is_default DESC, id DESC",
        (session["uid"],)
    ).fetchall()
    return render_template("account/addresses.html", addresses=rows)


@app.route("/account/profile", methods=["GET", "POST"])
@login_required
def account_profile():
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (session["uid"],)).fetchone()
    if request.method == "POST":
        db.execute(
            "UPDATE users SET full_name = ?, phone = ? WHERE id = ?",
            (request.form.get("full_name"), request.form.get("phone"), session["uid"])
        )
        db.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("account_profile"))
    return render_template("account/profile.html", user=user)


@app.route("/account/favorites")
@login_required
def account_favorites():
    db = get_db()
    rows = db.execute(
        """SELECT p.* FROM favorites f JOIN products p ON p.id = f.product_id
           WHERE f.user_id = ? AND p.is_active = 1 ORDER BY f.created_at DESC""",
        (session["uid"],)
    ).fetchall()
    return render_template("account/favorites.html", products=rows)


@app.route("/favorites/toggle/<int:pid>", methods=["POST"])
@login_required
def favorite_toggle(pid):
    db = get_db()
    existing = db.execute(
        "SELECT id FROM favorites WHERE user_id = ? AND product_id = ?",
        (session["uid"], pid)
    ).fetchone()
    if existing:
        db.execute("DELETE FROM favorites WHERE id = ?", (existing["id"],))
    else:
        db.execute("INSERT INTO favorites (user_id, product_id) VALUES (?, ?)",
                   (session["uid"], pid))
    db.commit()
    return redirect(request.referrer or url_for("shop"))


@app.route("/account/orders/<int:order_id>/reorder", methods=["POST"])
@login_required
def account_reorder(order_id):
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id = ? AND user_id = ?",
                       (order_id, session["uid"])).fetchone()
    if not order:
        abort(404)
    items = db.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
    cart_l = _get_cart()
    for it in items:
        if it["product_id"]:
            cart_l.append({"key": secrets.token_hex(8), "type": "product",
                           "product_id": it["product_id"], "qty": it["quantity"]})
    session.modified = True
    flash("Items added to cart.", "success")
    return redirect(url_for("cart"))


# ─── Admin ─────────────────────────────────────────────────────────────────
from security.decorators import admin_required


@app.route("/admin")
@admin_required
def admin_dashboard():
    db = get_db()
    kpis = {
        "users": db.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"],
        "products": db.execute("SELECT COUNT(*) AS n FROM products WHERE is_active = 1").fetchone()["n"],
        "orders": db.execute("SELECT COUNT(*) AS n FROM orders").fetchone()["n"],
        "revenue": db.execute(
            "SELECT COALESCE(SUM(total), 0) AS s FROM orders WHERE payment_status = 'paid'"
        ).fetchone()["s"],
    }
    recent_orders = db.execute(
        "SELECT * FROM orders ORDER BY created_at DESC LIMIT 10"
    ).fetchall()
    return render_template("admin/dashboard.html", kpis=kpis, recent_orders=recent_orders)


@app.route("/admin/products")
@admin_required
def admin_products():
    db = get_db()
    rows = db.execute(
        """SELECT p.*, c.name AS category_name FROM products p
           LEFT JOIN categories c ON c.id = p.category_id
           ORDER BY p.created_at DESC"""
    ).fetchall()
    return render_template("admin/products.html", products=rows)


@app.route("/admin/products/new", methods=["GET", "POST"])
@admin_required
def admin_product_new():
    db = get_db()
    cats = db.execute("SELECT * FROM categories ORDER BY sort_order").fetchall()
    if request.method == "POST":
        _admin_product_save(None, cats)
        return redirect(url_for("admin_products"))
    return render_template("admin/product_form.html", product=None, categories=cats)


@app.route("/admin/products/<int:pid>/edit", methods=["GET", "POST"])
@admin_required
def admin_product_edit(pid):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
    if not product:
        abort(404)
    cats = db.execute("SELECT * FROM categories ORDER BY sort_order").fetchall()
    if request.method == "POST":
        _admin_product_save(product, cats)
        return redirect(url_for("admin_products"))
    return render_template("admin/product_form.html", product=product, categories=cats)


def _admin_product_save(product, categories):
    db = get_db()
    from security.sanitize import sanitize_slug, clean_text
    slug = sanitize_slug(request.form.get("slug") or request.form.get("name") or "")
    fields = {
        "slug": slug,
        "name": clean_text(request.form.get("name"), 120),
        "short_description": clean_text(request.form.get("short_description"), 200),
        "description": clean_text(request.form.get("description"), 2000),
        "ingredients": clean_text(request.form.get("ingredients"), 500),
        "category_id": int(request.form.get("category_id") or 0) or None,
        "price_mur": float(request.form.get("price_mur") or 0) or None,
        "price_ngn": float(request.form.get("price_ngn") or 0) or None,
        "price_usd": float(request.form.get("price_usd") or 0) or None,
        "is_active": 1 if request.form.get("is_active") else 0,
        "is_featured": 1 if request.form.get("is_featured") else 0,
    }
    if product:
        sets = ", ".join(f"{k} = ?" for k in fields)
        db.execute(f"UPDATE products SET {sets} WHERE id = ?",
                   list(fields.values()) + [product["id"]])
    else:
        cols = ", ".join(fields.keys())
        marks = ", ".join("?" for _ in fields)
        db.execute(f"INSERT INTO products ({cols}) VALUES ({marks})", list(fields.values()))
    db.commit()
    flash("Product saved.", "success")


@app.route("/admin/products/<int:pid>/delete", methods=["POST"])
@admin_required
def admin_product_delete(pid):
    db = get_db()
    db.execute("UPDATE products SET is_active = 0 WHERE id = ?", (pid,))
    db.commit()
    flash("Product archived.", "success")
    return redirect(url_for("admin_products"))


@app.route("/admin/orders")
@admin_required
def admin_orders():
    db = get_db()
    status = request.args.get("status") or ""
    q = ["SELECT * FROM orders"]
    params = []
    if status:
        q.append("WHERE order_status = ?")
        params.append(status)
    q.append("ORDER BY created_at DESC LIMIT 200")
    rows = db.execute(" ".join(q), params).fetchall()
    return render_template("admin/orders.html", orders=rows, status=status)


@app.route("/admin/orders/<int:order_id>", methods=["GET", "POST"])
@admin_required
def admin_order_detail(order_id):
    db = get_db()
    order = db.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not order:
        abort(404)
    if request.method == "POST":
        new_status = request.form.get("order_status")
        if new_status in ("pending", "confirmed", "shipped", "delivered", "cancelled"):
            db.execute("UPDATE orders SET order_status = ? WHERE id = ?",
                       (new_status, order_id))
            db.commit()
            flash("Order updated.", "success")
            return redirect(url_for("admin_order_detail", order_id=order_id))
    items = db.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
    return render_template("admin/order_detail.html", order=order, items=items)


@app.route("/admin/users")
@admin_required
def admin_users():
    db = get_db()
    rows = db.execute(
        "SELECT id, email, full_name, phone, role, status, created_at FROM users ORDER BY created_at DESC"
    ).fetchall()
    return render_template("admin/users.html", users=rows)


@app.route("/admin/users/<int:uid>")
@admin_required
def admin_user_detail(uid):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
    if not user:
        abort(404)
    orders = db.execute(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC", (uid,)
    ).fetchall()
    return render_template("admin/user_detail.html", user=user, orders=orders)


@app.route("/admin/users/export.csv")
@admin_required
def admin_users_export():
    import csv, io
    db = get_db()
    rows = db.execute(
        "SELECT id, email, full_name, phone, role, status, created_at FROM users ORDER BY id"
    ).fetchall()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "email", "full_name", "phone", "role", "status", "created_at"])
    for r in rows:
        w.writerow([r["id"], r["email"], r["full_name"], r["phone"] or "",
                    r["role"], r["status"], r["created_at"]])
    from flask import make_response
    resp = make_response(buf.getvalue())
    resp.headers["Content-Type"] = "text/csv"
    resp.headers["Content-Disposition"] = "attachment; filename=kcb_users.csv"
    return resp


@app.route("/admin/reports")
@admin_required
def admin_reports():
    db = get_db()
    by_region = db.execute(
        """SELECT region, COUNT(*) AS orders, COALESCE(SUM(total), 0) AS revenue
           FROM orders WHERE payment_status = 'paid' GROUP BY region"""
    ).fetchall()
    top_products = db.execute(
        """SELECT name_snapshot, SUM(quantity) AS units, SUM(line_total) AS revenue
           FROM order_items GROUP BY name_snapshot ORDER BY units DESC LIMIT 10"""
    ).fetchall()
    daily = db.execute(
        """SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS n, COALESCE(SUM(total),0) AS rev
           FROM orders WHERE payment_status = 'paid'
           GROUP BY day ORDER BY day DESC LIMIT 30"""
    ).fetchall()
    return render_template("admin/reports.html",
                           by_region=by_region, top_products=top_products, daily=daily)


@app.route("/admin/builder", methods=["GET", "POST"])
@admin_required
def admin_builder():
    db = get_db()
    if request.method == "POST":
        db.execute(
            """INSERT INTO builder_options (option_type, name, price_mur, price_ngn, price_usd, sort_order)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (request.form.get("option_type"),
             request.form.get("name"),
             float(request.form.get("price_mur") or 0),
             float(request.form.get("price_ngn") or 0),
             float(request.form.get("price_usd") or 0),
             int(request.form.get("sort_order") or 0))
        )
        db.commit()
        flash("Option added.", "success")
        return redirect(url_for("admin_builder"))
    options = db.execute(
        "SELECT * FROM builder_options ORDER BY option_type, sort_order"
    ).fetchall()
    return render_template("admin/builder_config.html", options=options)


@app.route("/wellness")
def wellness():
    db = get_db()
    posts = db.execute(
        "SELECT * FROM blogs WHERE is_published = 1 ORDER BY created_at DESC"
    ).fetchall()
    return render_template("public/wellness.html", posts=posts)


@app.route("/wellness/<slug>")
def wellness_post(slug):
    db = get_db()
    post = db.execute(
        "SELECT * FROM blogs WHERE slug = ? AND is_published = 1", (slug,)
    ).fetchone()
    if not post:
        abort(404)
    return render_template("public/wellness_post.html", post=post)


@app.template_filter("mdinline")
def _md_inline(text):
    import re as _re
    from markupsafe import Markup, escape as _escape
    t = str(_escape(text or ""))
    t = _re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = _re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)
    return Markup(t)


@app.route("/about")
def about(): return render_template("public/about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        flash("Thanks — we've received your message.", "success")
        return redirect(url_for("contact"))
    return render_template("public/contact.html")


@app.route("/faq")
def faq(): return render_template("public/faq.html")


@app.route("/privacy")
def privacy(): return render_template("public/privacy.html")


@app.route("/terms")
def terms(): return render_template("public/terms.html")


@app.route("/refund-policy")
def refund_policy(): return render_template("public/refund.html")


@app.route("/shipping-policy")
def shipping_policy(): return render_template("public/shipping.html")


@app.errorhandler(404)
def _err_404(e): return render_template("public/error.html"), 404


@app.errorhandler(500)
def _err_500(e): return render_template("public/error.html"), 500


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        # We deliberately do not reveal whether the address exists.
        flash("If that email is registered, we've sent reset instructions.", "success")
        return redirect(url_for("login"))
    return render_template("auth/forgot.html")


@app.route("/admin/users/<int:uid>/status", methods=["POST"])
@admin_required
def admin_user_status(uid):
    from security.audit import audit
    new_status = request.form.get("status")
    if new_status not in ("active", "suspended", "deleted"):
        abort(400)
    db = get_db()
    target = db.execute("SELECT id, email, status FROM users WHERE id = ?", (uid,)).fetchone()
    if not target:
        abort(404)
    if target["id"] == session.get("uid"):
        flash("You cannot change your own status.", "error")
        return redirect(url_for("admin_user_detail", uid=uid))
    db.execute("UPDATE users SET status = ? WHERE id = ?", (new_status, uid))
    db.commit()
    audit(db, "user.status_change", entity="user", entity_id=uid,
          meta={"from": target["status"], "to": new_status, "email": target["email"]})
    flash(f"User marked {new_status}.", "success")
    return redirect(url_for("admin_user_detail", uid=uid))


@app.route("/healthz")
def healthz():
    """Liveness probe for Docker/Railway. Cheap, no DB hit."""
    return {"status": "ok"}, 200


@app.route("/readyz")
def readyz():
    """Readiness probe — verifies we can hit the DB."""
    try:
        get_db().execute("SELECT 1").fetchone()
        return {"status": "ready"}, 200
    except Exception as e:
        return {"status": "degraded", "error": str(e)}, 503

# ─── Auth ──────────────────────────────────────────────────────────────────
from flask import request, redirect, url_for, session, flash, render_template, abort
from security.passwords import verify_password
from security.ratelimit import hit as _rate_hit


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        ip = request.headers.get("X-Forwarded-For", request.remote_addr or "x")
        if not _rate_hit(f"login:{ip}", limit=5, window_sec=60):
            flash("Too many login attempts. Please try again in a minute.", "error")
            return render_template("auth/login.html")
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        db = get_db()
        u = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if u and verify_password(password, u["password_hash"]) and u["status"] == "active":
            session.clear()
            session["uid"] = u["id"]
            session["role"] = u["role"]
            session.permanent = True
            db.execute("UPDATE users SET last_login_at = datetime('now') WHERE id = ?", (u["id"],))
            db.commit()
            return redirect(url_for("root"))
        flash("Invalid credentials.", "error")
    return render_template("auth/login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    from security.passwords import hash_password
    from security.validators import valid_email, valid_phone, valid_name, valid_password_strength

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        full_name = (request.form.get("full_name") or "").strip()
        phone = (request.form.get("phone") or "").strip()
        password = request.form.get("password") or ""

        if not valid_email(email):
            flash("Invalid email.", "error")
        elif not valid_name(full_name):
            flash("Please enter your full name.", "error")
        elif phone and not valid_phone(phone):
            flash("Invalid phone number.", "error")
        elif not valid_password_strength(password):
            flash("Password must be 8+ chars with letters & digits.", "error")
        else:
            db = get_db()
            if db.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
                flash("Email already registered.", "error")
            else:
                db.execute(
                    "INSERT INTO users (email, password_hash, full_name, phone) VALUES (?, ?, ?, ?)",
                    (email, hash_password(password), full_name, phone or None)
                )
                db.commit()
                flash("Account created — please sign in.", "success")
                return redirect(url_for("login"))
    return render_template("auth/register.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Signed out.", "success")
    return redirect(url_for("root"))

@app.route("/")
def root():
    return redirect(url_for("home"))


@app.route("/store")
def store_select():
    return render_template("public/store_select.html")


@app.route("/store/<region>", methods=["POST"])
def store_set(region):
    region = (region or "").upper()
    if region not in ("NG", "MU", "GL"):
        abort(400)
    session["region"] = region
    return redirect(url_for("home"))


@app.route("/home")
def home():
    db = get_db()
    featured = db.execute(
        "SELECT * FROM products WHERE is_featured = 1 AND is_active = 1 LIMIT 8"
    ).fetchall()
    return render_template("public/home.html", featured=featured)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
