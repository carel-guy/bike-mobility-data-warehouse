"""FastAPI authentication microservice using a client-credentials flow."""

from datetime import datetime, timedelta, timezone
import json
from typing import Optional

from fastapi import Depends, FastAPI, Form, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from jose import JWTError, jwt
from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import (
    Credentials,
    Token,
    TokenValidationRequest,
    TokenValidationResponse,
)
from .security import verify_secret

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit])

app = FastAPI(title="Bike Auth Service", version="0.2.0")
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

http_credentials = HTTPBasic(auto_error=False)


async def credentials_form(
    grant_type: str = Form(regex="^client_credentials$"),
    client_id: Optional[str] = Form(default=None),
    client_secret: Optional[str] = Form(default=None),
    basic_credentials: Optional[HTTPBasicCredentials] = Depends(http_credentials),
) -> Credentials:
    """
    Extract OAuth2 client credentials from either form data or HTTP Basic.

    OAuth2 client credentials allow credentials via the Authorization header
    or via the body, so we support both and always return a normalized object.
    """
    if grant_type != "client_credentials":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="grant_type must be client_credentials",
        )

    if basic_credentials and basic_credentials.username and basic_credentials.password:
        client_id = basic_credentials.username
        client_secret = basic_credentials.password

    if not client_id or not client_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Client credentials must be provided via form or HTTP Basic Auth",
        )

    return Credentials(client_id=client_id, client_secret=client_secret)


def fetch_client(db: Session, client_id: str) -> Optional[dict]:
    """Load an active client from the database."""
    query = text(
        """
        SELECT client_id, secret_hash, roles
        FROM service_clients
        WHERE client_id = :client_id AND active = TRUE
        """
    )
    return db.execute(query, {"client_id": client_id}).mappings().one_or_none()


def build_token(client_id: str, roles: list[str]) -> Token:
    """Create a signed JWT for the given client."""
    expires_delta = timedelta(minutes=settings.token_expire_minutes)
    now = datetime.now(timezone.utc)
    payload = {
        "sub": client_id,
        "roles": roles,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    jwt_token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return Token(access_token=jwt_token, expires_in=int(expires_delta.total_seconds()))


@app.get("/", tags=["Status"])
def healthcheck():
    """Lightweight readiness probe."""
    return {"status": "ok"}


@app.post(
    "/token",
    response_model=Token,
    tags=["Authentication"],
    summary="Obtain an access token using client credentials OAuth2 flow",
)
def token(credentials: Credentials = Depends(credentials_form), db: Session = Depends(get_db)):
    """Issue a JWT if the client_id/client_secret pair is valid."""
    client_row = fetch_client(db, credentials.client_id)
    if not client_row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client credentials",
        )

    if not verify_secret(credentials.client_secret, client_row["secret_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client credentials",
        )

    roles = client_row["roles"]
    if isinstance(roles, str):
        roles = json.loads(roles)

    return build_token(credentials.client_id, roles)


@app.post("/token/validate", response_model=TokenValidationResponse, tags=["Authentication"])
def validate_token(payload: TokenValidationRequest):
    """Validate a JWT and expose select claims."""
    try:
        decoded = jwt.decode(
            payload.token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError:
        return TokenValidationResponse(active=False)

    expires_at = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
    return TokenValidationResponse(
        active=True,
        client_id=decoded.get("sub"),
        roles=decoded.get("roles", []),
        expires_at=expires_at,
    )
