# =============================================================================
# Multi-stage Dockerfile — Frontend SPA (Nginx)
# =============================================================================
# Security: Non-root (UID 1001), read-only FS, no build tools in runtime.
# =============================================================================

# ── Stage 1: Builder ──
FROM node:22-alpine AS builder

WORKDIR /build

COPY package.json package-lock.json* ./
RUN npm ci --ignore-scripts

COPY . .
RUN npm run build

# ── Stage 2: Runtime ──
FROM nginx:1.27-alpine AS runtime

# Security: remove default config
RUN rm -rf /etc/nginx/conf.d/default.conf /usr/share/nginx/html/*

# Copy custom nginx config and built assets
COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=builder /build/dist /usr/share/nginx/html

# Non-root user setup
RUN chown -R 1001:0 /usr/share/nginx/html /var/cache/nginx /var/log/nginx /tmp && \
    chmod -R g+w /var/cache/nginx /var/log/nginx /tmp

USER 1001

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:8080/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
