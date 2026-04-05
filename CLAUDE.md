# KubeAuto Day IDP Build

## What This Is

Building a production-grade Internal Developer Platform on EKS from scratch.
Every component is deployed via ArgoCD GitOps. No kubectl apply after Phase 2.

This repo serves three purposes:
1. The live demo platform for the KubeAuto Day Europe 2026 talk
2. An open-source reference IDP (Apache 2.0)
3. Evidence for the AI Platform Building Scorecard

## How To Work

1. Read `spec/BUILD-SPEC.md` for the full build plan
2. Check which phase you're on by looking at `spec/SCORECARD.md`
3. Write tests FIRST (`tests/test_phase_0X_*.py`), then implement until they pass
4. After each component, update the scorecard with honest scores
5. Commit after each working component, not after each file

## TDD Protocol (5-Step Cycle)

Every feature follows this exact cycle. No shortcuts.

1. **Write a failing test** for the specific component/behavior
2. **Run the test** to confirm it fails (expected failure, not import error)
3. **Write minimal code** to make the test pass
4. **Run the test** to confirm it passes
5. **Refactor** if needed, re-run test to confirm still green

If you skip step 2 (confirming the test actually fails first), the test may be
vacuously passing and proves nothing.

## Rules

- Everything after Phase 2 must be deployed as an ArgoCD Application
- No secrets in Git. Ever. Use External Secrets Operator.
- No kubectl apply in production namespaces after ArgoCD is running
- Every Helm install needs a values.yaml in the gitops/apps/ directory
- Test before you commit. If tests don't pass, don't commit.
- When you get stuck on IAM, re-read the AWS docs. Don't guess trust policies.
- Update `spec/SCORECARD.md` honestly after completing each component
- Record what went wrong in the scorecard notes column

## ABOUTME Comments

All code files (Python, Shell, YAML with logic) start with a brief 2-line comment:
```
# ABOUTME: Line 1 - what this file is
# ABOUTME: Line 2 - what it does / why it exists
```

This applies to every file created in every phase. Check before committing.

## No Mocks, Stubs, or Fallbacks

All tests hit real infrastructure. No mocked Kubernetes clients, no stubbed AWS
calls, no fake HTTP servers. Tests require a running cluster. If the cluster
isn't available, the test fails — that's correct behavior.

Never add fallback mechanisms. Code should fail explicitly rather than silently
fall back to defaults.

## Type Hints

Every Python file (tests, helpers, conftest, scripts) includes type annotations
on all function signatures. Use `-> None` for functions with no return value.

## Progress Indicators

Any operation that might cause the user to wait must show progress output.
wait_helpers.py and kubectl_helpers.py print progress dots or status messages.

## Per-Component Commits

Commit after each logical component passes its tests, not after each phase.
Each commit must:
1. Be on the `staging` branch (verify with `git branch --show-current`)
2. Pass the full test suite (`uv run pytest tests/ -v`), not just current phase
3. Have a professional, technical commit message (no AI/Claude references)
4. Include only the files for that component

## Pre-Push Verification

Before EVERY push to remote:
```bash
git branch --show-current  # Must show "staging"
git pull origin staging
uv run pytest tests/ -v    # Full test suite
git push origin staging
```

## Scorecard Updates

Update `spec/SCORECARD.md` after EACH individual component, not in batch.
Include the scorecard update in that component's commit.

## Architecture Decision Records

Write an ADR in `docs/adr/` (MADR format) when a significant technology or
pattern choice is made. Commit alongside the component it documents.

## Completion Protocol

Output `<promise>PHASEX_DONE</promise>` (where X is the phase number) ONLY when
ALL test criteria for that phase pass. Do not output the promise if any test fails.

Output `<promise>ALL_PHASES_COMPLETE</promise>` only when all 7 phases are done.

## Skills

See `.claude/skills/` for patterns on specific components. Read the relevant
skill file BEFORE generating any config for that component.

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
