# =============================================================================
# Makefile — Developer Workflow Shortcuts
# =============================================================================

.PHONY: help dev down build lint test scan clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Local Development ──

dev: ## Start all services (docker-compose up)
	docker compose up -d --build
	@echo "\n✅ Services starting..."
	@echo "  Backend:  http://localhost:8000"
	@echo "  Frontend: http://localhost:5173"
	@echo "  Keycloak: http://localhost:8080 (admin/admin)"

down: ## Stop all services
	docker compose down

logs: ## Tail all service logs
	docker compose logs -f

# ── Build & Validate ──

build: ## Build all container images
	docker compose build

lint: ## Run all linters
	cd backend && uv run ruff check . && uv run mypy app/
	cd frontend && npx tsc --noEmit

test: ## Run backend tests
	cd backend && uv run pytest --cov --cov-report=term-missing

# ── Security Scanning ──

scan: ## Trivy scan backend image
	trivy image fastapi-oidc-backend:latest --severity HIGH,CRITICAL

scan-fs: ## Trivy filesystem scan
	trivy fs . --severity HIGH,CRITICAL --exit-code 1

secrets: ## Scan for leaked secrets
	gitleaks detect --source . --verbose

# ── Helm ──

helm-lint: ## Lint Helm chart
	helm lint helm/fastapi-oidc-app/ -f helm/fastapi-oidc-app/values-dev.yaml

helm-template: ## Render Helm templates
	helm template test helm/fastapi-oidc-app/ -f helm/fastapi-oidc-app/values-dev.yaml

# ── Terraform ──

tf-init: ## Initialize Terraform
	cd terraform && terraform init -backend=false

tf-validate: ## Validate Terraform
	cd terraform && terraform validate

tf-fmt: ## Format Terraform files
	cd terraform && terraform fmt -recursive

# ── Cleanup ──

clean: ## Remove all containers, volumes, and build artifacts
	docker compose down -v --rmi local
	cd backend && rm -rf .venv .ruff_cache .mypy_cache .pytest_cache htmlcov
	cd frontend && rm -rf node_modules dist
