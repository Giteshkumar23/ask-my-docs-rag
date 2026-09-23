"""Security utilities: JWT creation/verification and password hashing.

Usage
-----
    from app.core.security import create_access_token, verify_token, hash_password

    token = create_access_token({"sub": str(user.id)})
    payload = verify_token(token)        # raises HTTPException on failure
    hashed = hash_password("secret")
    ok = verify_password("secret", hashed)
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# --------------------------------------------------------------------------- #
# Password hashing
# --------------------------------------------------------------------------- #

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Return the bcrypt hash of *plain*."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return ``True`` if *plain* matches the *hashed* password."""
    return _pwd_context.verify(plain, hashed)


# --------------------------------------------------------------------------- #
# JWT
# --------------------------------------------------------------------------- #

_ALGORITHM = "HS256"
_DEFAULT_EXPIRE_MINUTES = 60 * 24  # 24 hours


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Encode *data* into a signed JWT and return the token string.

    Parameters
    ----------
    data:
        Payload to encode.  ``"sub"`` (subject) is the conventional key for
        the user identifier.
    expires_delta:
        Optional custom expiry.  Defaults to 24 hours.
    """
    to_encode = data.copy()
    expire = datetime.now(tz=timezone.utc) + (
        expires_delta or timedelta(minutes=_DEFAULT_EXPIRE_MINUTES)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=_ALGORITHM)


def verify_token(token: str) -> Dict[str, Any]:
    """Decode and verify *token*, raising 401 on any failure.

    Returns
    -------
    dict
        The decoded JWT payload.

    Raises
    ------
    :class:`fastapi.HTTPException`
        401 Unauthorized when the token is invalid or expired.
    """
    try:
        payload: Dict[str, Any] = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[_ALGORITHM]
        )
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
