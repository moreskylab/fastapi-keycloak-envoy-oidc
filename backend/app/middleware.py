"""
Security middleware stack (OWASP A01, A05, A09).

- Security response headers (X-Frame-Options, CSP, HSTS, etc.)
- Request ID generation/propagation for distributed tracing
- Strict CORS — no wildcards
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject OWASP-recommended security headers into every response.

    Mitigates: clickjacking (X-Frame-Options), MIME sniffing (X-Content-Type-Options),
    XSS (CSP), information leakage (Server, Referrer-Policy, Permissions-Policy).
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)

        # OWASP A05: Security Misconfiguration — hardened headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "0"  # Modern browsers use CSP instead
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'"
        )

        # Prevent server version leakage
        response.headers["Server"] = "secured"

        # HSTS — enforce HTTPS in production
        if settings.environment != "dev":
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )

        return response


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Generate or propagate X-Request-ID for distributed tracing.

    If the incoming request has an X-Request-ID header (e.g., from Envoy),
    use it. Otherwise, generate a new UUID v4. The ID is set on the
    request state and echoed back in the response.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


def configure_middleware(app: FastAPI) -> None:
    """Wire all middleware into the FastAPI application.

    Order matters: outermost middleware executes first.
    """
    # CORS — strict origin, no wildcards (OWASP A05)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.cors_origin],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
        max_age=3600,
    )

    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # Request ID tracing
    app.add_middleware(RequestIdMiddleware)
