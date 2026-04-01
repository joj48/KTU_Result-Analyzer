from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings, Settings

bearer_scheme = HTTPBearer(auto_error=False)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(
    data: dict[str, Any],
    settings: Settings | None = None,
) -> str:
    """Return a signed JWT access token valid for ACCESS_TOKEN_EXPIRE_MINUTES."""
    cfg = settings or get_settings()
    payload = data.copy()
    payload["exp"] = _utcnow() + timedelta(minutes=cfg.access_token_expire_minutes)
    payload["type"] = "access"
    return jwt.encode(payload, cfg.jwt_secret, algorithm=cfg.jwt_algorithm)


def create_refresh_token(
    data: dict[str, Any],
    settings: Settings | None = None,
) -> str:
    """Return a signed JWT refresh token valid for REFRESH_TOKEN_EXPIRE_DAYS."""
    cfg = settings or get_settings()
    payload = data.copy()
    payload["exp"] = _utcnow() + timedelta(days=cfg.refresh_token_expire_days)
    payload["type"] = "refresh"
    return jwt.encode(payload, cfg.jwt_secret, algorithm=cfg.jwt_algorithm)


def decode_token(token: str, settings: Settings | None = None) -> dict[str, Any]:
    """Decode and validate a JWT token. Raises HTTPException on failure."""
    cfg = settings or get_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, cfg.jwt_secret, algorithms=[cfg.jwt_algorithm])
        return payload
    except JWTError:
        raise credentials_exception


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    """FastAPI dependency — extracts and validates the bearer access token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
        )
    return user_id
