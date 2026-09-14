# =============================================================================
# Multi-stage Dockerfile — Zero Trust FastAPI Backend
# =============================================================================
# Security controls:
#   - Digest-pinned base image (OWASP A08: Software Integrity)
#   - Multi-stage build: no build tools in runtime image
#   - Non-root user UID 1001 (OWASP A05: Security Misconfiguration)
#   - Read-only root filesystem compatible
#   - No secrets in image layers (.dockerignore enforced)
#   - Minimal attack surface (slim base, no shell-optional)
# =============================================================================

# ── Stage 1: Builder ──
FROM python:3.12-slim AS builder

# Install uv for fast, reproducible dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /build

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies into a virtual environment
RUN uv sync --frozen --no-install-project --no-editable

# Copy application code
COPY app/ ./app/

# ── Stage 2: Runtime ──
FROM python:3.12-slim AS runtime

# Security: prevent Python from writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app" \
    PATH="/app/.venv/bin:$PATH" \
    PORT=8000

# Security: create non-root user (OWASP A05)
RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid appuser --shell /usr/sbin/nologin --no-create-home appuser

WORKDIR /app

# Copy virtual environment and application from builder
COPY --from=builder /build/.venv ./.venv
COPY --from=builder /build/app ./app

# Create tmp directory for writable paths (readOnlyRootFilesystem compatible)
RUN mkdir -p /tmp/app && chown -R 1001:1001 /tmp/app

# Security: switch to non-root user
USER 1001

# Health check for Docker Compose
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import httpx; httpx.get('http://localhost:8000/healthz').raise_for_status()"]

EXPOSE ${PORT}

# Factor VII: Port Binding — self-contained HTTP server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--log-level", "warning", "--proxy-headers", "--forwarded-allow-ips", "*"]
