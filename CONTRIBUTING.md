# Contributing

This repository is a reference IDP built for KubeAuto Day Europe 2026.
Contributions that improve documentation, fix bugs, or add useful patterns
are welcome.

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a branch from `staging` (never work on `main` directly)
4. Make your changes
5. Submit a pull request to `staging`

## Development Workflow

### Branch Strategy

```
staging → main (via PR only)
```

- All work happens on `staging` or feature branches off `staging`
- `main` is updated only via pull request merges from `staging`
- Direct pushes to `main` are blocked

### Test-Driven Development

Every change follows the TDD cycle:

1. Write a failing test
2. Confirm the test fails
3. Write minimal code to pass
4. Confirm the test passes
5. Refactor if needed

Tests are in `tests/` and require a running EKS cluster (no mocks).

### Running Tests

```bash
uv run pytest tests/ -v
```

Tests are organized by phase (`test_phase_01_foundation.py` through
`test_phase_07_hardening.py`).

### Pre-commit Hooks

Install the pre-commit framework:

```bash
pip install pre-commit
pre-commit install
pre-commit install --hook-type pre-push
```

Eight hooks run automatically on commit:
- gitleaks (secret scanning)
- yamllint (YAML validation)
- kubeconform (Kubernetes schema validation)
- terraform validate
- helm lint
- trivy (Dockerfile scanning)
- image allowlist (registry enforcement)
- namespace scope (phase-scoped validation)

### Commit Messages

Use this format:

```
phase-X/component: brief description

Optional longer explanation.
```

Or conventional commit format:

```
feat(argocd): add application for new service
fix(kyverno): correct webhook config for chart 3.7.0
docs(security): update RBAC documentation
```

Do not include AI/Claude references in commit messages.

## Adding a New Component

1. Write tests in `tests/test_phase_0X_*.py`
2. Create Kubernetes manifests in the appropriate directory
3. Create an ArgoCD Application in `gitops/apps/`
4. Ensure all Kyverno policies are satisfied (labels, probes, limits)
5. Update `spec/SCORECARD.md` with honest scores
6. Write an ADR in `docs/adr/` if making a significant technology choice

## Code Standards

- **Python**: Type hints on all functions, ABOUTME headers on all files
- **YAML**: 2-space indentation, validated by yamllint
- **Terraform**: `terraform fmt` compliant
- **Kubernetes**: Passes kubeconform strict mode

## What Not to Do

- No secrets in Git (use External Secrets Operator)
- No `kubectl apply` in production namespaces (use ArgoCD)
- No mock/stub/fallback mechanisms in tests
- No unrelated changes bundled in a PR

## License

By contributing, you agree that your contributions will be licensed under
the Apache 2.0 License.
