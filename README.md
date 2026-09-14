# 🔐 Zero Trust OIDC Platform

> **FastAPI · Keycloak · Envoy Gateway · Cilium · EKS**

A production-grade, defense-in-depth boilerplate demonstrating edge-enforced authentication offloading, Identity Federation (Google OIDC via Keycloak), and fine-grained Application Role-Based Access Control (RBAC).

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Internet                                  │
└─────────────────────┬───────────────────────────────────────────┘
                      │
         ┌────────────▼────────────┐
         │    Envoy Gateway        │  ← JWT validation (edge)
         │    (Gateway API)        │    Rate limiting, WAF
         └──┬──────────────┬───┬──┘
            │              │   │
   ┌────────▼──┐  ┌────────▼─┐ │  ┌──────────────┐
   │ Frontend  │  │ Backend  │ │  │  Keycloak     │
   │ (Nginx)   │  │ (FastAPI)│ └──▶  (OIDC IdP)   │
   └───────────┘  └────┬─────┘    └──────┬────────┘
                       │                  │
                  JWKS fetch         ┌────▼─────┐
                                     │PostgreSQL│
                                     └──────────┘
```

### Security Layers

| Layer | Component | Controls |
|-------|-----------|----------|
| **Edge** | Envoy Gateway | JWT validation, rate limiting, TLS termination |
| **Network** | Cilium eBPF | L7 microsegmentation, WireGuard encryption, FQDN egress |
| **Admission** | Kyverno | Non-root, resource limits, image registry restrictions |
| **Runtime** | Falco | Syscall anomaly detection |
| **Application** | FastAPI | OWASP headers, input validation, RBAC assertion |
| **Supply Chain** | Cosign + Trivy | Image signing, vulnerability scanning, SAST |

## Quick Start (Local Dev)

```bash
# Clone the repo
git clone https://github.com/REPLACE_ORG/fastapi-keycloak-envoy-oidc.git
cd fastapi-keycloak-envoy-oidc

# Copy env template
cp .env.example .env

# Start all services
make dev

# Access:
# Frontend:  http://localhost:5173
# Backend:   http://localhost:8000/docs
# Keycloak:  http://localhost:8080 (admin/admin)
```

### Demo Users

| Username | Password | Roles | Access |
|----------|----------|-------|--------|
| `demo-user` | `demo` | `default_user` | `/api/secure/me` ✅, `/api/secure/rbac-check` ❌ |
| `premium-user` | `premium` | `default_user`, `premium_user` | `/api/secure/me` ✅, `/api/secure/rbac-check` ✅ |

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/public` | None | Service metadata |
| GET | `/api/secure/me` | JWT | User identity claims |
| GET | `/api/secure/rbac-check` | JWT + `premium_user` role | RBAC-gated endpoint |
| GET | `/healthz` | None | Liveness probe |
| GET | `/readyz` | None | Readiness probe |
| GET | `/metrics` | None | Prometheus metrics |

## Project Structure

```
├── backend/           # FastAPI application (Python 3.12, uv)
├── frontend/          # TypeScript SPA (Vite, keycloak-js)
├── keycloak/          # Realm export with Google OIDC federation
├── helm/              # Helm chart with per-env value files
├── kustomize/         # Kustomize overlays (dev/staging/prod)
├── cilium/            # eBPF network policies (L7, FQDN)
├── policies/          # Kyverno admission policies
├── argocd/            # App-of-Apps + ApplicationSet
├── terraform/         # EKS + VPC + Karpenter + Cilium + IRSA
├── .github/workflows/ # CI/CD pipelines (PR, Build, Deploy, Scan)
├── docker-compose.yml # Local development
└── Makefile           # Developer workflow shortcuts
```

## 12-Factor Compliance

| Factor | Implementation |
|--------|---------------|
| I. Codebase | Single Git repo, all environments from same source |
| II. Dependencies | `uv.lock` (Python), `package-lock.json` (Node) |
| III. Config | Environment variables via `.env` / ESO from Vault |
| IV. Backing Services | PostgreSQL as attached resource |
| V. Build/Release/Run | Multi-stage Docker → OCI artifacts → ArgoCD |
| VI. Processes | Stateless containers, session in JWT |
| VII. Port Binding | Self-contained HTTP server (uvicorn/nginx) |
| VIII. Concurrency | KEDA autoscaling, Karpenter node provisioning |
| IX. Disposability | SIGTERM handling, preStop hooks, graceful drain |
| X. Dev/Prod Parity | Same Docker images, same Helm chart, env values differ |
| XI. Logs | Structured JSON → stdout → Alloy → Loki |
| XII. Admin Processes | Helm hooks for DB migrations |

## Production Deployment

See the [Implementation Plan](docs/implementation-plan.md) for the full production deployment guide covering:

- EKS cluster provisioning with Cilium CNI
- HashiCorp Vault with KMS auto-unseal
- ArgoCD GitOps with sync wave orchestration
- cert-manager with Let's Encrypt DNS-01
- Argo Rollouts for canary deployments
- LGTM observability stack (Loki, Grafana, Tempo, Mimir)

## License

Apache-2.0