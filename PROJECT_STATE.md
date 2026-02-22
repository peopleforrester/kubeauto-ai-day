# Project State: KubeAuto AI Day IDP (KubeCon EU 2026)

## Current Plan
Platform build complete (27/27 components, 59 tests, 73.8% toil reduction).
Eight Guardrails reconciliation done — Layer 3 fully implemented, Layers 1-2
documented with implementation options. Presentation prep in progress.

## Task Checklist
- [x] EKS-based Internal Developer Platform with AI assistance
- [x] Unicorn Party demo app (v2.0.2) with interactive experience
- [x] ALB ingresses for Unicorn Party and E-Commerce Frontend
- [x] Demo runbook with external URLs, known issues, failure fallbacks
- [x] Phase 8 collateral: version accuracy, scorecard, QR codes
- [x] PR workflow with staging → main merges
- [x] Eight Guardrails reconciliation analysis
- [x] Eight Guardrails full implementation (Layer 1 + Layer 2 hooks, documentation)
- [ ] Build actual slides from `collateral/slide-outline.md`
- [ ] Demo runbook 3x end-to-end practice
- [ ] Practice run with timer (target 27 min)
- [ ] Fix test1 DNS (add explicit CNAME in Namecheap)
- [ ] Screenshot fallbacks for live demo
## Progress
- **Last completed**: Eight Guardrails full implementation — all three layers active
- **Next step**: Presentation prep (slides, demo practice, timer runs)
- **Remaining items**: See `REMAINING-ITEMS.md`

## Key Documents
- `REMAINING-ITEMS.md` — Full "what's left" checklist
- `docs/EIGHT-GUARDRAILS-RECONCILIATION.md` — Layer-by-layer gap analysis
- `docs/WALKTHROUGH.md` — Complete Three-Layer architecture + Eight Guardrails mapping
- `spec/SCORECARD.md` — Final scorecard (27/27, 73.8% toil reduction)

## Branch & Test Status
- **Branch**: staging
- **Clean**: yes
- **Tests**: passing (59 tests)

## Session Notes
- Every component built with AI-assisted development and TDD
- Every correction cycle documented for the talk
- All three guardrail layers implemented:
  - Layer 3 (Kubernetes): 8/8 guardrails (Kyverno, Falco, RBAC, ESO, ArgoCD, etc.)
  - Layer 2 (Claude Code): 7/8 guardrails (PreToolUse, PostToolUse, Stop, SessionStart)
  - Layer 1 (Git hooks): 8/8 guardrails (gitleaks, yamllint, kubeconform, terraform, helm, trivy, image-allowlist, namespace-scope)
- Pre-commit hooks: 8 hooks, all passing
