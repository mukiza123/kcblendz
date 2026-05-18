# Testing guide

KCBlendz has two layers of automated tests, all driven by Python's standard
`unittest` runner (also reachable via pytest because of `pytest.ini`).

## Layout

- `tests.py` — single test module, organised into classes:
  - `CardValidationTests`, `CardBrandTests`, `CardFormValidationTests`
  - `RegistrationTests`, `LoginTests`, `LogoutTests`, `PasswordHashingTests`
  - `CSRFTests`, `AdminAccessTests`, `UploadValidationTests`
  - `CartAddTests`, `CartUpdateRemoveTests`, `CartSubtotalTests`
  - `CheckoutFlowTests`, `OrderCreationTests`
  - `AdminDashboardTests`, `AdminProductCRUDTests`
  - `BuilderPricingAPITests`

## Conventions

1. Pure logic (Luhn, brand detection, password hashing, validators) uses a
   plain `unittest.TestCase` — fast, no DB.
2. Anything that hits the DB inherits `_BaseDB`, which provisions an isolated
   SQLite file in `/tmp` and seeds the default admin user before every test.
3. Use `_csrf(client, path)` and `_login(client, email, password)` from the
   top of the module — they're the only auth helpers you need.
4. Every state-changing request must include `_csrf` in the form — the CSRF
   middleware returns 400 otherwise.

## Run

```bash
# Everything
py -m unittest tests.py -v

# A single class
py -m unittest tests.CardValidationTests -v

# A single test
py -m unittest tests.CardValidationTests.test_luhn_accepts_valid_visa -v

# With coverage
coverage run -m unittest tests.py && coverage report
```

## Adding tests

- Put new tests in the smallest class that fits, or create a new one.
- One assertion per test where possible.
- Avoid time-based assertions — they flake under CI load.
