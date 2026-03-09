## Summary

<!-- 1-3 bullet points describing what this PR does and why -->

## Phase / Component

<!-- Which build phase and component does this PR affect? e.g., Phase 3 / Kyverno -->

## Changes

<!-- List the key changes. Reference files or ADRs where relevant. -->

## Test Plan

- [ ] `uv run pytest tests/ -v` passes locally
- [ ] Affected phase tests pass: `uv run pytest tests/test_phase_0X_*.py -v`
- [ ] ArgoCD applications sync cleanly (if GitOps manifests changed)
- [ ] `spec/SCORECARD.md` updated (if a scored component changed)

## Checklist

- [ ] All code files have ABOUTME headers
- [ ] Type hints on all function signatures
- [ ] No secrets committed (checked with gitleaks)
- [ ] Commit messages follow conventional format (`phase-X/component:` or `type(scope):`)
