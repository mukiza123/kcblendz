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

## Deployment

### Railway (recommended)

1. Push to GitHub.
2. Create a new Railway project, "Deploy from GitHub".
3. Railway auto-detects `railway.json` and the `Procfile`.
4. Add the variables from `.env.example` in the Railway dashboard.
5. Set `KCB_FORCE_SECURE=1` once your custom domain is on HTTPS.

### Heroku

```bash
heroku create kcblendz
heroku config:set KCB_SECRET="$(py -c 'import secrets;print(secrets.token_hex(32))')"
heroku config:set KCB_FORCE_SECURE=1
git push heroku main
heroku run flask --app app init-db
```

### Generic gunicorn host

```bash
gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 60 --preload
```

## API reference

KCBlendz is mostly server-rendered, but a few JSON endpoints exist for the
builder and ops tooling.

### `POST /api/builder/price`

Compute the live price of a custom-built smoothie.

Request body (JSON):

```json
{
  "cup_size": 1,
  "base": 2,
  "fruits": [4, 5],
  "sweeteners": [],
  "addons": [9],
  "boosters": []
}
```

Response (JSON):

```json
{ "price": 285.0, "currency": "MU" }
```

### `GET /healthz`

Liveness probe — returns `{"status":"ok"}` without touching the DB.

### `GET /readyz`

Readiness probe — runs `SELECT 1`; returns 503 if the DB is unreachable.

### `GET /admin/users/export.csv`

(admin) Streams a CSV of every user account.

### `GET /sitemap.xml`, `GET /robots.txt`

SEO endpoints.
