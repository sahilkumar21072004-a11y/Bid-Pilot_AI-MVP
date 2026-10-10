"""Database-backed failed-login throttling shared across app workers."""
from __future__ import annotations

import hashlib
import hmac
import time

from fastapi import HTTPException

from .config import settings
from .store import connect

MAX_LOGIN_FAILURES = 5
LOGIN_WINDOW_SECONDS = 15 * 60


def _keys(client_host: str, username: str) -> tuple[str, str]:
    secret = settings.session_secret.encode("utf-8")
    normalized_username = username.strip().casefold()
    values = (f"ip:{client_host or 'unknown'}", f"user:{normalized_username}")
    return tuple(hmac.new(secret, value.encode("utf-8"), hashlib.sha256).hexdigest() for value in values)


def enforce_login_rate_limit(client_host: str, username: str) -> None:
    now = int(time.time())
    keys = _keys(client_host, username)
    with connect() as db:
        row = db.execute(
            "SELECT MAX(locked_until) FROM login_attempts WHERE key IN (?,?)",
            keys,
        ).fetchone()
    blocked_until = int(row[0] or 0) if row else 0
    if blocked_until > now:
        retry_after = blocked_until - now
        raise HTTPException(
            status_code=429,
            detail="Too many failed login attempts. Try again later.",
            headers={"Retry-After": str(retry_after)},
        )


def record_login_failure(client_host: str, username: str) -> None:
    now = int(time.time())
    cutoff = now - LOGIN_WINDOW_SECONDS
    blocked_until = now + LOGIN_WINDOW_SECONDS
    sql = """
        INSERT INTO login_attempts(key,window_started_at,failures,locked_until)
        VALUES(?,?,1,0)
        ON CONFLICT(key) DO UPDATE SET
            window_started_at = CASE
                WHEN login_attempts.window_started_at <= ? THEN ?
                ELSE login_attempts.window_started_at
            END,
            failures = CASE
                WHEN login_attempts.window_started_at <= ? THEN 1
                ELSE login_attempts.failures + 1
            END,
            locked_until = CASE
                WHEN login_attempts.locked_until > ? THEN login_attempts.locked_until
                WHEN login_attempts.window_started_at <= ? THEN 0
                WHEN login_attempts.failures + 1 >= ? THEN ?
                ELSE 0
            END
    """
    with connect() as db:
        for key in _keys(client_host, username):
            db.execute(sql, (key, now, cutoff, now, cutoff, now, cutoff, MAX_LOGIN_FAILURES, blocked_until))


def clear_login_failures(client_host: str, username: str) -> None:
    with connect() as db:
        db.execute("DELETE FROM login_attempts WHERE key IN (?,?)", _keys(client_host, username))
