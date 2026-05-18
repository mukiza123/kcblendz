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

