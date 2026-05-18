# Contributing to KCBlendz

Thanks for your interest in improving KCBlendz! Quick rules:

1. **Conventional commits.** `feat`, `fix`, `refactor`, `style`, `chore`, `test`,
   `docs`. Scope is the subsystem (`backend`, `ui`, `security`, `db`, `ci`, …).
2. **Branch naming.** `<type>/<short-summary>` — e.g. `feat/builder-coupons`.
3. **Tests first.** Every new route or pure function ships with a test in
   `tests.py`. See `docs/TESTING.md`.
4. **No secrets in commits.** `.env` is gitignored — keep it that way.
5. **Security changes** need a Security review (see `SECURITY.md`).

Run `make help` to see all developer tasks.
