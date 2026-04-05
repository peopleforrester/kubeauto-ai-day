# Project State: KubeAuto AI Day IDP (KubeCon EU 2026)

## Current Plan
Senior developer review remediation complete (2026-04-06). All critical,
high, and medium priority items resolved. Ready for public repo prep.

## Task Checklist — Review Remediation (2026-04-06)

### Critical (Fix Immediately)
- [x] Fix hardcoded `/home/ollama/` paths in `tests/test_phase_07_hardening.py` → use `pathlib.Path`
- [x] Extract Grafana basic auth constant from 3 test files into `conftest.py`

### High Priority
- [x] Fix namespace list inconsistency: `test_phase_01_foundation.py` now matches `conftest.py` (8 namespaces)
- [x] Remove duplicate Falco rules in `security/falco/custom-rules.yaml`
- [x] Fix `wait_helpers.py` type hints: `object` → `CoreV1Api`
- [x] Deduplicate `load_kube_config()` — single autouse session fixture in conftest

### Medium Priority
- [x] Update `pyproject.toml` description
- [x] Update `.current-phase` to `7`
- [x] Add `.dockerignore` to `sample-app/`
- [x] Fix `Optional` import style in `tests/helpers/kubectl_helpers.py`

### Not In Scope (documented only)
- AWS account ID parameterization (14 files) — needs SETUP.md doc, not a code fix
- Grafana admin password — already has ESO comment, acceptable for demo
- Recording scripts test coverage — out of scope
- ArgoCD retry config on child apps — low risk for demo

## Previous Work
- [x] EKS-based Internal Developer Platform with AI assistance (27/27 components)
- [x] 59 integration tests, all phases
- [x] Eight Guardrails full implementation (all three layers)
- [x] Demo runbook, presentation collateral

## Progress
- **Last completed**: Senior review remediation — all 10 items fixed
- **Next step**: Presentation prep (slides, demo practice, timer runs)
- **Branch**: staging
- **Tests**: need cluster to verify (syntax check passes)

## Key Documents
- `spec/SCORECARD.md` — Final scorecard (27/27, 73.8% toil reduction)
- `docs/EIGHT-GUARDRAILS-RECONCILIATION.md` — Layer-by-layer gap analysis
- `docs/WALKTHROUGH.md` — Three-Layer architecture + Eight Guardrails mapping
