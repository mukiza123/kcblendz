"""
KCBlendz — Premium Smoothie & Wellness E-commerce Platform
Monolithic Flask application with SQLite.

Implements every requirement from:
  - KCBLENDZ_WEBSITE_REQUIREMENT_DOCUMENT.pdf
  - Capstone project proposal (master prompt)

Run:
    pip install -r requirements.txt
    python app.py
    => http://localhost:5000
"""
import os
import sqlite3
import secrets
import hashlib
import hmac
import json
import re
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from urllib.parse import urlparse

from flask import (
    Flask, render_template, request, redirect, url_for, session,
    flash, jsonify, abort, g, send_from_directory, make_response
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import Markup, escape

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
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


@app.template_filter("mdinline")
def md_inline(text):
    """Render inline markdown safely: **bold**, *italic*, `code`,
    [label](url). Escapes HTML first so article content can't inject markup,
    then applies a small, safe subset. Fixes the literal ** showing on the
    wellness article pages."""
    from markupsafe import Markup, escape
    s = str(escape(text or ""))
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"`(.+?)`",
               r'<code class="bg-gray-100 px-1 rounded">\1</code>', s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)",
               r'<a href="\2" class="link" target="_blank" rel="noopener">\1</a>', s)
    return Markup(s)


# ─────────────────────────────────────────────────────────────────────────────
# DATABASE — schema, connection, init
# ─────────────────────────────────────────────────────────────────────────────
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    phone TEXT,
    role TEXT NOT NULL DEFAULT 'customer',  -- customer | admin
    status TEXT NOT NULL DEFAULT 'active',  -- active | suspended | deleted
    region TEXT,                            -- preferred region NG / MU / GL
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_login_at TEXT
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
    is_available_global INTEGER NOT NULL DEFAULT 0,  -- only shelf-stable for Global
    is_featured INTEGER NOT NULL DEFAULT 0,
    is_bestseller INTEGER NOT NULL DEFAULT 0,
    is_new INTEGER NOT NULL DEFAULT 0,
    tags TEXT,  -- comma separated: tropical,detox,energy,...
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    is_active INTEGER NOT NULL DEFAULT 1
);
"""
