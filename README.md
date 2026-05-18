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
