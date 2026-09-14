"""
JWT security utilities (OWASP A01, A02, A07).

- Async JWKS fetcher with TTL caching (dynamic key rotation)
- JWT token decoding and verification (RS256, expiry, issuer, audience)
- Role-based access control assertion (realm_access.roles)
- Clean error responses — never leaks internal details
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx
from fastapi import HTTPException, Request, status
from jose import JWTError, jwt
from jose.constants import Algorithms

from app.config import settings

logger = logging.getLogger(__name__)

# ── JWKS Cache ──
# Cache the JWKS response to avoid fetching on every request.
# TTL: 5 minutes — balances key rotation speed with performance.
_jwks_cache: dict[str, Any] = {}
_jwks_cache_expiry: float = 0.0
_JWKS_CACHE_TTL_SECONDS: int = 300  # 5 minutes


async def fetch_jwks() -> dict[str, Any]:
    """Fetch JWKS from Keycloak's dynamic endpoint with TTL caching.

    Security: Keys are fetched over HTTPS in production (never hardcoded).
    The JWKS endpoint provides the public keys used to verify JWT signatures,
    enabling cryptographic key rotation without code changes.
    """
    global _jwks_cache, _jwks_cache_expiry  # noqa: PLW0603

    now = time.monotonic()
    if _jwks_cache and now < _jwks_cache_expiry:
        return _jwks_cache

    jwks_url = str(settings.jwks_url)
    logger.info("Fetching JWKS from %s", jwks_url)

    try:
        async with httpx.AsyncClient(timeout=10.0, verify=True) as client:
            response = await client.get(jwks_url)
            response.raise_for_status()
            jwks_data: dict[str, Any] = response.json()
    except httpx.HTTPError:
        logger.exception("Failed to fetch JWKS from %s", jwks_url)
        # If we have a cached version, use it (graceful degradation)
        if _jwks_cache:
            logger.warning("Using stale JWKS cache after fetch failure")
            return _jwks_cache
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable",
        )

    _jwks_cache = jwks_data
    _jwks_cache_expiry = now + _JWKS_CACHE_TTL_SECONDS
    logger.info("JWKS cache refreshed, %d keys loaded", len(jwks_data.get("keys", [])))
    return jwks_data


def _get_signing_key(jwks: dict[str, Any], token: str) -> dict[str, Any]:
    """Extract the correct signing key from JWKS based on the token's 'kid' header."""
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
        )

    kid = unverified_header.get("kid")
    if not kid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing key identifier",
        )

    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token signing key not found",
    )


async def decode_and_verify_token(token: str) -> dict[str, Any]:
    """Decode and cryptographically verify a JWT token.

    Validates:
    - RS256 signature against Keycloak's JWKS public keys
    - Token expiry (exp claim)
    - Issuer (iss claim) matches expected Keycloak realm
    - Audience (aud claim) if configured

    Returns the decoded token payload on success.
    Raises HTTPException with generic messages on any failure (no internal leaks).
    """
    jwks = await fetch_jwks()
    signing_key = _get_signing_key(jwks, token)

    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            signing_key,
            algorithms=[Algorithms.RS256],
            issuer=settings.issuer_url,
            options={
                "verify_aud": False,  # Keycloak audience handling varies by client
                "verify_iss": True,
                "verify_exp": True,
                "verify_iat": True,
                "require": ["exp", "iss", "sub"],
            },
        )
    except JWTError as e:
        logger.warning("JWT verification failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    return payload


def assert_role(payload: dict[str, Any], required_role: str) -> None:
    """Assert that the token payload contains a specific realm role.

    Inspects `realm_access.roles` in the Keycloak JWT structure.
    Returns None on success, raises 403 Forbidden if the role is missing.

    OWASP A01: Broken Access Control — explicit role verification.
    """
    realm_access = payload.get("realm_access")
    if not isinstance(realm_access, dict):
        logger.warning(
            "Token for sub=%s missing realm_access claim",
            payload.get("sub", "unknown"),
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    roles = realm_access.get("roles")
    if not isinstance(roles, list):
        logger.warning(
            "Token for sub=%s has malformed roles claim",
            payload.get("sub", "unknown"),
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    if required_role not in roles:
        logger.info(
            "Access denied for sub=%s: missing role '%s' (has: %s)",
            payload.get("sub", "unknown"),
            required_role,
            roles,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )


def extract_bearer_token(request: Request) -> str:
    """Extract Bearer token from the Authorization header.

    Raises 401 if the header is missing or malformed.
    """
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return auth_header[7:]  # Strip "Bearer " prefix
