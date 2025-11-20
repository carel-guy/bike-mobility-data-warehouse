"""Pydantic schemas leveraged by the authentication service."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Credentials(BaseModel):
    """Incoming client credentials extracted from a form or HTTP Basic."""

    client_id: str
    client_secret: str


class Token(BaseModel):
    """OAuth2-style token response."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenValidationRequest(BaseModel):
    """Payload used to validate a token."""

    token: str


class TokenValidationResponse(BaseModel):
    """Normalized token validation output."""

    active: bool
    client_id: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None


class TokenValidationRequest(BaseModel):
    token: str


class TokenValidationResponse(BaseModel):
    active: bool
    username: Optional[str] = None
    issued_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    roles: list[str] = []
