"""Utility helpers for hashing and verifying client secrets."""

import hashlib
import secrets


def hash_secret(secret: str) -> str:
    """Hash a client secret using SHA-256."""
    return hashlib.sha256(secret.encode()).hexdigest()


def verify_secret(secret: str, expected_hash: str) -> bool:
    """Check whether the provided secret matches the stored hash."""
    digest = hash_secret(secret)
    return secrets.compare_digest(digest, expected_hash)
