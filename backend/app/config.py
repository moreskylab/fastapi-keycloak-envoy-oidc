"""
Application configuration via environment variables (12-Factor: Factor III).

All configuration is sourced from environment variables with validation at startup.
Zero hardcoded credentials. Fail-fast on misconfiguration.
"""

from __future__ import annotations

from pydantic import HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Security controls:
    - All secrets from env vars (injected by ESO from Vault in production)
    - URL validation prevents misconfigured endpoints
    - Fail-fast: invalid config crashes the app at startup, not at runtime
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Keycloak Configuration ──
    keycloak_url: HttpUrl = HttpUrl("http://keycloak:8080")
    keycloak_realm: str = "oidc-demo"

    # ── JWKS Configuration (derived from Keycloak) ──
    jwks_url: HttpUrl | None = None

    # ── CORS Configuration (strict: no wildcards) ──
    cors_origin: str = "http://localhost:5173"

    # ── Server Configuration (Factor VII: Port Binding) ──
    port: int = 8000
    host: str = "0.0.0.0"  # noqa: S104 — bind all interfaces inside container
    workers: int = 1

    # ── Logging ──
    log_level: str = "INFO"
    environment: str = "dev"

    # ── Application Metadata ──
    app_name: str = "fastapi-oidc-backend"
    app_version: str = "0.1.0"

    @field_validator("jwks_url", mode="before")
    @classmethod
    def derive_jwks_url(cls, v: str | None, info: object) -> str:
        """Derive JWKS URL from Keycloak URL + realm if not explicitly set."""
        if v is not None:
            return v
        # Access other field values via info.data
        data = getattr(info, "data", {})
        keycloak_url = str(data.get("keycloak_url", "http://keycloak:8080")).rstrip("/")
        realm = data.get("keycloak_realm", "oidc-demo")
        return f"{keycloak_url}/realms/{realm}/protocol/openid-connect/certs"

    @property
    def issuer_url(self) -> str:
        """Construct the expected JWT issuer URL."""
        base = str(self.keycloak_url).rstrip("/")
        return f"{base}/realms/{self.keycloak_realm}"


# Singleton settings instance — validated once at import time
settings = Settings()
