"""Short-lived signed bearer tokens for the single-admin local MVP login."""
import base64
import hashlib
import hmac
import json
import time
import os

from .config import settings

PASSWORD_ROUNDS = 310_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PASSWORD_ROUNDS)
    return f"pbkdf2_sha256${PASSWORD_ROUNDS}${_b64(salt)}${_b64(digest)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds, salt_text, digest_text = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_text + "=" * (-len(salt_text) % 4))
        expected = base64.urlsafe_b64decode(digest_text + "=" * (-len(digest_text) % 4))
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(rounds))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def issue_token(username: str, role: str = "admin") -> str:
    payload = _b64(json.dumps({"sub": username, "role": role, "exp": int(time.time()) + 8 * 60 * 60}, separators=(",", ":")).encode())
    signature = _b64(hmac.new(settings.session_secret.encode(), payload.encode(), hashlib.sha256).digest())
    return f"{payload}.{signature}"


def verify_token(token: str) -> dict[str, str] | None:
    if not settings.session_secret or "." not in token:
        return None
    payload, signature = token.split(".", 1)
    expected = _b64(hmac.new(settings.session_secret.encode(), payload.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        decoded = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
        data = json.loads(decoded)
        if int(data.get("exp", 0)) <= int(time.time()):
            return None
        return {"username": str(data["sub"]), "role": str(data["role"])}
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None
