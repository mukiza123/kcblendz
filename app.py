"""
KCBlendz — Premium Smoothie & Wellness E-commerce Platform.

Monolithic Flask application backed by SQLite.
"""
from pathlib import Path
from flask import Flask

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__)


@app.route("/")
def root():
    return "KCBlendz is alive."


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
