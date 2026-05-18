# Security module

Contains the building blocks that protect KCBlendz:

- `passwords.py`  — hashing & verification
- `validators.py` — email / phone / payload validators
- `csrf.py`       — synchronizer-token CSRF
- `decorators.py` — `login_required`, `admin_required`, `region_required`
- `headers.py`    — security HTTP headers
- `uploads.py`    — file-type validation & filename safety
- `audit.py`      — append-only audit log helpers

Every PR that touches one of these files needs a Security review.
