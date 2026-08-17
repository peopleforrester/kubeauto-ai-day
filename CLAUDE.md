# KubeAuto Day IDP Build

Building a production-grade Internal Developer Platform on EKS from scratch. Every component deployed via ArgoCD GitOps after Phase 2.

This repo serves three purposes:
1. Live demo platform for KubeAuto Day Europe 2026 talk
2. Open-source reference IDP (Apache 2.0)
3. Evidence for the AI Platform Building Scorecard

**Stack**: EKS 1.34+, ArgoCD 3.2+, Kyverno 1.17+, Backstage 1.46+, Falco, OTel Collector 0.140+, Grafana 12.x, cert-manager 1.19+, Terraform EKS module ~>21.0, Python (uv, pytest)

## How To Work

1. Read `spec/BUILD-SPEC.md` for the full build plan
2. Check current phase via `spec/SCORECARD.md`
3. Write tests first (`tests/test_phase_0X_*.py`), then implement until they pass
4. Update scorecard after each component with honest scores
5. Commit after each working component, not after each file

## Commands

```bash
uv run pytest tests/ -v    # Full test suite

# Pre-push verification
git branch --show-current  # Must show "staging"
git pull origin staging
uv run pytest tests/ -v
git push origin staging
```

## Project-Specific Rules

- **Everything after Phase 2 must be an ArgoCD Application**
- **No secrets in Git** — use External Secrets Operator
- **No kubectl apply** in production namespaces after ArgoCD is running
- Every Helm install needs a `values.yaml` in `gitops/apps/`
- **All tests hit real infrastructure** — no mocked Kubernetes clients, no stubbed AWS calls. If cluster isn't available, test fails.
- **Commits on `staging` branch only** (verify with `git branch --show-current`)
- Each commit must pass full test suite, not just current phase
- When stuck on IAM, re-read the AWS docs — don't guess trust policies

## Scorecard Protocol

Update `spec/SCORECARD.md` after EACH individual component (not in batch). Include the scorecard update in that component's commit. Record what went wrong in the notes column.

## Architecture Decision Records

Write ADRs in `docs/adr/` (MADR format) for significant technology or pattern choices. Commit alongside the component they document.

## Completion Protocol

Output `<promise>PHASEX_DONE</promise>` (X = phase number) ONLY when ALL test criteria pass. Output `<promise>ALL_PHASES_COMPLETE</promise>` only when all 7 phases are done.

## Skills

See `.claude/skills/` for component-specific patterns. Read the relevant skill file BEFORE generating config for that component.

## Technology Versions (deployed)

`docs/VERSION-MAP.md` is the single source of truth for component versions.
The list below mirrors that file — keep it in sync if either changes.

- EKS: 1.34
- ArgoCD: 3.3.0 (Helm chart 9.4.2)
- Kyverno: 1.17.0 (Helm chart 3.7.0)
- Backstage: 1.9.1 (Helm chart 2.6.3 — chart appVersion 1.46+ wraps image 1.9.1)
- Falco: 0.43.0 / Helm chart 8.0.0 (CNCF Graduated, eBPF driver)
- OTel Collector: 0.145.0
- Grafana: 12.3.3 / Prometheus 3.9.1 via kube-prometheus-stack 82.1.0
- cert-manager: 1.19.3
- Terraform EKS module: ~> 21.0
- Instance type: m7i.xlarge
- Pod Identity primary, IRSA fallback for specific addons
