"""JWT validation helpers for the data service."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from .config import settings

bearer_scheme = HTTPBearer(
    scheme_name="Bearer",
    description="Paste the access token returned by the auth service.",
    auto_error=False,
)


def decode_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> dict:
    """Decode and verify the bearer token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:  # pragma: no cover - simple error propagation
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc
    return payload


def require_user(payload: dict = Depends(decode_token)) -> dict:
    """Dependency used by any endpoint that needs a valid user token."""
    return payload


def require_admin(payload: dict = Depends(decode_token)) -> dict:
    """Ensure the caller owns the 'admin' role."""
    roles = payload.get("roles", [])
    if "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )
    return payload
