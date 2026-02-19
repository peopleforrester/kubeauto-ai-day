# Phase 2: GitOps Bootstrap — Prompt Log

## Summary

- **Start time:** 2026-02-17 ~14:00 EST
- **End time:** 2026-02-17 ~14:35 EST
- **Total AI time:** 16 min (ArgoCD 8 + App-of-Apps 5 + Sync Waves 3)
- **Correction prompts:** 3 (ArgoCD 1, App-of-Apps 1, Sync Waves 1)
- **Components:** ArgoCD Install + Config, App-of-Apps Pattern, Sync Waves + Ordering

*Note: Prompts reconstructed from git history, scorecard notes, and session data.*

---

## Prompt 1 (Phase 2, ~14:00)
**Type:** Initial
**Prompt:** Write Phase 2 tests, then install ArgoCD 3.2+ via Helm and set up app-of-apps pattern.
**Result:** Partial — ArgoCD installed but chart version mapping was wrong
**Time spent:** 8 min
**Correction needed:** Yes — skill file said chart 7.x but actual chart was 9.x for ArgoCD 3.2.6
**Notes:** RBAC config and values.yaml correct first try. 30s reconciliation for demo. The chart version → app version mapping is non-obvious.

## Prompt 2 (Phase 2, ~14:08)
**Type:** Correction
**Prompt:** App-of-Apps root stuck in Progressing — ArgoCD can't access private GitHub repo.
**Result:** Success after creating repo secret
**Time spent:** 5 min
**Correction needed:** Yes — needed Kubernetes Secret with GitHub PAT
**Notes:** No error in Application status, just stuck Progressing. Secret must have `argocd.argoproj.io/secret-type=repository` label.

## Prompt 3 (Phase 2, ~14:13)
**Type:** Initial then correction
**Prompt:** Set up sync waves for deployment ordering and write drift detection test.
**Result:** Partial — sync waves correct, drift test needed fix
**Time spent:** 3 min
**Correction needed:** Yes — test added a new label (not detected) instead of modifying a managed field
**Notes:** ArgoCD 3.x annotation-based tracking only monitors fields ArgoCD manages. Adding a new label via kubectl is not drift.

## Test Results
- 17 tests passing after Phase 2
- Commits: `66bde7c` (14:16), `4bde270` (14:21)
