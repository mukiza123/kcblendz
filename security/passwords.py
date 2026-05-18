"""Password hashing & verification (werkzeug pbkdf2)."""
from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(plain: str) -> str:
    if not plain or len(plain) < 8:
        raise ValueError("Password must be at least 8 characters.")
    return generate_password_hash(plain, method="pbkdf2:sha256", salt_length=16)


def verify_password(plain: str, hashed: str) -> bool:
    if not plain or not hashed:
        return False
    return check_password_hash(hashed, plain)
