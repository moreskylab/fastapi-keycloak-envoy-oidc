# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | ✅ Current          |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead, please email: **security@REPLACE-DOMAIN.com**

### Response SLA

| Severity   | Response Time | Fix SLA    |
|------------|--------------|------------|
| Critical   | 4 hours      | 24 hours   |
| High       | 1 business day | 72 hours |
| Medium     | 3 business days | 2 weeks |
| Low        | 5 business days | Next release |

## Security Architecture

This project implements defense-in-depth with the following layers:

1. **Edge (Envoy Gateway)**: JWT validation, rate limiting, WAF
2. **Network (Cilium)**: L7 microsegmentation, WireGuard encryption, FQDN egress control
3. **Admission (Kyverno)**: Policy enforcement for pods, images, and configurations
4. **Runtime (Falco)**: Syscall-level anomaly detection
5. **Application (FastAPI)**: Input validation, RBAC, OWASP headers
6. **Supply Chain**: Cosign image signing, Trivy scanning, SAST

## Security Scanning Schedule

- **Every PR**: Trivy FS scan, Semgrep SAST, Helm lint
- **Every merge to main**: Trivy image scan, cosign signing
- **Nightly**: Full dependency audit, Gitleaks secret scan
- **Continuous**: Falco runtime detection, Cilium flow monitoring
