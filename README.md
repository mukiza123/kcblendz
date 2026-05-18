# KCBlendz — Premium Smoothie & Wellness E-commerce Platform

KCBlendz is a multi-region (Mauritius, Nigeria, Global) e-commerce platform for
premium smoothies, juices and wellness drinks.

## Stack
- **Backend**: Flask 3 (monolith, `app.py`)
- **Database**: SQLite (`kcblendz.db`)
- **Frontend**: Server-rendered Jinja2 templates + TailwindCSS
- **Deployment**: Railway / Heroku (gunicorn + nixpacks)

## Status
🚧 Under active development.

## Installation

```bash
# Clone & enter
git clone https://github.com/your-org/kcblendz.git
cd kcblendz

# Create virtualenv and install deps
py -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Copy env template and edit
cp .env.example .env

# Initialize the database (seeds admin@kcblendz.com / Admin1234)
flask --app app init-db

# Run the dev server
py app.py
```

Then open <http://localhost:5000>.

## Environment variables

| Variable           | Purpose                                                 | Default      |
| ------------------ | ------------------------------------------------------- | ------------ |
| `KCB_SECRET`       | Flask session signing key. Set to a high-entropy value. | random/dev   |
| `KCB_DB_PATH`      | Path to the SQLite database file.                       | `kcblendz.db`|
| `KCB_FORCE_SECURE` | Set to `1` behind HTTPS to mark session cookies Secure. | `0`          |
| `PORT`             | Web server bind port (injected by Railway/Heroku).      | `5000`       |

See `.env.example` for a template. Never commit `.env`.
