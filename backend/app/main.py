"""
FastAPI application entrypoint.

Three endpoint tiers demonstrating Zero Trust defense-in-depth:
1. /api/public       → No auth required (metadata endpoint)
2. /api/secure/me    → Valid JWT required (Envoy pre-validates, FastAPI re-validates)
3. /api/secure/rbac-check → JWT + realm role "premium_user" required (RBAC)

Health probes at /healthz (liveness) and /readyz (readiness).
Prometheus metrics at /metrics via instrumentator.

12-Factor: Factor IX (Disposability) — graceful SIGTERM shutdown.
12-Factor: Factor XI (Logs) — structured JSON to stdout.
"""

from __future__ import annotations

import logging
import signal
import sys
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Request
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.logging_config import setup_logging
from app.middleware import configure_middleware
from app.security import (
    assert_role,
    decode_and_verify_token,
    extract_bearer_token,
    fetch_jwks,
)

# ── Initialize structured logging before anything else ──
setup_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager (12-Factor: Factor IX).

    Startup: pre-warm JWKS cache, log configuration.
    Shutdown: graceful drain of in-flight requests.
    """
    # ── Startup ──
    logger.info(
        "Starting %s v%s in %s mode",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )

    # Pre-warm the JWKS cache to avoid cold-start latency on first request
    try:
        await fetch_jwks()
        logger.info("JWKS cache pre-warmed successfully")
    except Exception:
        logger.warning("JWKS pre-warm failed — will retry on first request")

    yield

    # ── Shutdown ──
    logger.info("Graceful shutdown initiated — draining in-flight requests")


def create_app() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs" if settings.environment == "dev" else None,
        redoc_url=None,
        openapi_url="/openapi.json" if settings.environment == "dev" else None,
        lifespan=lifespan,
    )

    # Wire middleware stack
    configure_middleware(app)

    # Prometheus metrics
    Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        excluded_handlers=["/healthz", "/readyz", "/metrics"],
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

    # Register routes
    _register_routes(app)

    # SIGTERM handler for graceful shutdown (Factor IX)
    signal.signal(signal.SIGTERM, _handle_sigterm)

    return app


def _handle_sigterm(signum: int, frame: Any) -> None:
    """Handle SIGTERM for graceful container shutdown."""
    logger.info("Received SIGTERM — shutting down gracefully")
    sys.exit(0)


def _register_routes(app: FastAPI) -> None:
    """Register all application routes."""

    # ── Health Probes ──

    @app.get("/healthz", tags=["probes"], include_in_schema=False)
    async def liveness() -> dict[str, str]:
        """Kubernetes liveness probe — is the process alive?"""
        return {"status": "ok"}

    @app.get("/readyz", tags=["probes"], include_in_schema=False)
    async def readiness() -> dict[str, str]:
        """Kubernetes readiness probe — can the app serve traffic?

        Checks JWKS availability to ensure we can validate tokens.
        """
        try:
            await fetch_jwks()
            return {"status": "ready"}
        except Exception:
            return {"status": "not ready"}

    # ── Tier 1: Public Endpoint (no authentication) ──

    @app.get("/api/public", tags=["public"])
    async def public_metadata(request: Request) -> dict[str, Any]:
        """Public metadata endpoint — no authentication required.

        Returns non-sensitive service information for health dashboards
        and client discovery.
        """
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "keycloak_realm": settings.keycloak_realm,
            "request_id": getattr(request.state, "request_id", "unknown"),
        }

    # ── Tier 2: Authenticated Endpoint (valid JWT required) ──

    @app.get("/api/secure/me", tags=["secure"])
    async def get_current_user(request: Request) -> dict[str, Any]:
        """Return the authenticated user's identity claims.

        Defense-in-depth: Envoy Gateway validates the JWT at the edge (perimeter).
        This endpoint re-validates the Bearer token for:
        - Internal-only routes bypassing Envoy
        - Claim extraction for application logic
        - Additional validation the gateway cannot perform
        """
        token = extract_bearer_token(request)
        payload = await decode_and_verify_token(token)

        logger.info(
            "Authenticated access by sub=%s",
            payload.get("sub", "unknown"),
            extra={"request_id": getattr(request.state, "request_id", "unknown")},
        )

        return {
            "sub": payload.get("sub"),
            "email": payload.get("email"),
            "name": payload.get("name", payload.get("preferred_username")),
            "realm_roles": payload.get("realm_access", {}).get("roles", []),
            "token_issuer": payload.get("iss"),
            "request_id": getattr(request.state, "request_id", "unknown"),
        }

    # ── Tier 3: RBAC Endpoint (JWT + specific realm role) ──

    @app.get("/api/secure/rbac-check", tags=["secure"])
    async def rbac_check(request: Request) -> dict[str, Any]:
        """Role-based access control check — requires 'premium_user' role.

        OWASP A01 (Broken Access Control):
        - Token must be valid (signature, expiry, issuer)
        - Token must contain realm_access.roles including 'premium_user'
        - Returns 403 Forbidden with generic message if role is missing
        """
        token = extract_bearer_token(request)
        payload = await decode_and_verify_token(token)
        assert_role(payload, "premium_user")

        logger.info(
            "RBAC access granted for sub=%s (premium_user)",
            payload.get("sub", "unknown"),
            extra={"request_id": getattr(request.state, "request_id", "unknown")},
        )

        return {
            "message": "Premium access granted",
            "user": payload.get("preferred_username"),
            "role": "premium_user",
            "request_id": getattr(request.state, "request_id", "unknown"),
        }


# ── Application Instance ──
app = create_app()
