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

