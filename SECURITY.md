# Security policy

We take the security of KCBlendz and our customers' data seriously.

## Supported versions

Only the latest `main` branch receives security fixes. Older tags are not
maintained.

## Reporting a vulnerability

**Please do not file a public GitHub issue.**

Instead, email the security team at **security@kcblendz.com** with:

- A clear description of the issue and its impact
- Reproduction steps (a minimal PoC if you have one)
- Any logs, screenshots, or exploit artifacts

We aim to acknowledge reports within **48 hours** and to ship a fix within
**14 days** of confirmation for high-severity issues.

## Hardening already in place

- pbkdf2-sha256 password hashing (werkzeug)
- Synchronizer-token CSRF on every state-changing request
- HttpOnly + SameSite=Lax + Secure (when `KCB_FORCE_SECURE=1`) cookies
- Content-Security-Policy, X-Frame-Options: DENY, X-Content-Type-Options
- Sliding-window rate limit on login attempts (5 / minute / IP)
- Upload allow-list (png/jpg/jpeg/gif/webp) + path-traversal blocker
- Audit log for sensitive admin actions
- Account suspension status enforced on every request

## Out of scope

- Denial-of-service via brute-force volume
- Vulnerabilities requiring a compromised admin account
- Issues in dependencies already disclosed upstream
