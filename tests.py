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


class SmokeTests(unittest.TestCase):
    def test_root_responds(self):
        with kc.app.test_client() as c:
            r = c.get("/")
            self.assertIn(r.status_code, (200, 302))


if __name__ == "__main__":
    unittest.main(verbosity=2)
