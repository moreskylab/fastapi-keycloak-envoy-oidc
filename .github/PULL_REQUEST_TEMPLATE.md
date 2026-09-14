## Description

<!-- Describe your changes and their purpose -->

## Type of Change

- [ ] 🐛 Bug fix (non-breaking change)
- [ ] ✨ Feature (non-breaking change)
- [ ] 💥 Breaking change
- [ ] 🔒 Security fix
- [ ] 🏗️ Infrastructure change
- [ ] 📝 Documentation update

## Security Checklist

- [ ] No secrets or credentials are committed
- [ ] Container runs as non-root with read-only filesystem
- [ ] Resource limits (CPU/memory) are defined
- [ ] Liveness and readiness probes are present
- [ ] Input validation is implemented (OWASP A03)
- [ ] Error messages do not leak internal details

## Testing

- [ ] Unit tests pass (`make test`)
- [ ] Lint passes (`make lint`)
- [ ] Trivy scan passes (`make scan`)
- [ ] Helm lint passes (`make helm-lint`)

## Deployment

- [ ] Helm values updated if needed
- [ ] Cilium network policies reviewed
- [ ] Kyverno policies validated
