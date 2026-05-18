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

# ─── Auth ──────────────────────────────────────────────────────────────────
from flask import request, redirect, url_for, session, flash, render_template
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
    return "KCBlendz is alive."


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
