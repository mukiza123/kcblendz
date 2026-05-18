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

# ─── Auth ──────────────────────────────────────────────────────────────────
from flask import request, redirect, url_for, session, flash, render_template, abort
from security.passwords import verify_password


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
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
