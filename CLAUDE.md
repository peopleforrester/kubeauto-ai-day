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

These are the versions deployed on the demo cluster. Latest available noted where drifted.

- EKS: 1.34
- ArgoCD: 3.2.6 deployed (3.3.6 available; Helm chart 9.x)
- Kyverno: 1.17.1 (current; Helm chart 3.7.0)
- Backstage: 1.46+ (Helm chart 2.6.3, image 1.9.1; 1.49.3 available)
- Falco: CNCF Graduated, eBPF driver (Helm chart 7.x deployed; 8.0.1 available — major version)
- OTel Collector: 0.145.0 deployed (0.149.0 available; 0.x, no GA)
- Grafana: 12.x via kube-prometheus-stack 82.1.0 (82.18.0 available)
- cert-manager: 1.19+ (1.20.1 available)
- Terraform EKS module: ~>21.0 (21.17.0 latest)
- Instance type: m7i.xlarge
- Pod Identity primary, IRSA fallback for specific addons
