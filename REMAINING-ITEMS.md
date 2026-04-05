# Remaining Items — KubeAuto Day IDP

Last updated: 2026-04-06

## Status: Talk Complete, Post-Talk Phase

All 7 build phases done. 27/27 components scored. 59 tests passing.
KubeAuto Day Europe talk delivered March 23, 2026 in Amsterdam.
Senior developer review remediation completed April 6, 2026.

---

## Completed (Pre-Talk)

### 1. Build Actual Slides
- Source: `collateral/slide-outline.md` (19 slides, ~27 min)
- Status: **DONE**

### 2. Demo Runbook 3x End-to-End
- Source: `collateral/demo-runbook.md`
- Status: **DONE**

### 3. Practice Run with Timer
- Target: 27 minutes for 30-minute slot
- Status: **DONE**

### 4. Fix argocd DNS (Negative Cache)
- Issue: `argocd.ai-enhanced-devops.com` returned NXDOMAIN despite wildcard
- Root cause: Negative DNS cache (SOA shows 3601s negative TTL)
- Fix: Added explicit CNAME record in Namecheap for `argocd`
- Status: **DONE**

### 5. Screenshot Fallbacks for Live Demo
- Screenshots captured for: ArgoCD dashboard, Grafana dashboard, Backstage catalog,
  Unicorn Party app, E-Commerce Frontend
- Status: **DONE**

---

## Post-Talk: Should Do

### 6. Make Repo Public
- Currently private. Ready for public visibility.
- Pre-publish checklist: run `/gh-public-check`, verify no secrets, confirm
  `.gitignore` coverage, remove any private references
- AWS account ID (598274344262) appears in 14 files — document replacement
  process in SETUP.md before publishing

### 7. Publish Blog Post
- Draft exists at `collateral/blog-post-draft.md`
- Owner: Michael (manual task)

### 8. Post Social Media Thread
- Draft exists at `collateral/social-media-thread.md`
- Owner: Michael (manual task)

### 9. Cluster Teardown Decision
- Running at ~$0.57/hr ($410/month)
- Decision: Keep alive for post-talk demos or tear down?
- Teardown guide: `docs/TEARDOWN.md`

---

## Post-Talk: Nice to Have

### 10. Version Bumps (April 2026 drift)
- ArgoCD 3.3.6 available (project uses 3.2+)
- Falco Helm chart 8.0.1 available (project uses 7.x) — major version, review changelog
- kube-prometheus-stack 82.18.0 available (project uses 82.1.0)
- OTel Collector Helm chart 0.147.1 available (project uses 0.145.0)
- Skip unless cluster stays alive for continued demos

---

## Completed (During Build)

### ~~Eight Guardrails Reconciliation~~ DONE (2026-02-22)
- All three layers implemented

### ~~Git Tags for Phase Completion~~ DONE (2026-02-22)
- 8 annotated tags created: `phase-0-complete` through `phase-7-complete`

### ~~Guardrail Column in Scorecard~~ DONE (2026-02-22)
- Added "Guardrails" column to `spec/SCORECARD.md`

### ~~Senior Review Remediation~~ DONE (2026-04-06)
- 10 items fixed: hardcoded paths, type hints, DRY violations, stale metadata

---

## Decided: Not Doing

- **GitHub Actions CI**: Credit-limited, skip
- **Blog/social publishing**: Content exists, Michael handles scheduling
- **Known quirks** (ArgoCD app-of-apps OutOfSync, Kyverno CRD OutOfSync):
  Architectural characteristics, not bugs
- **Cluster cost optimization**: Acceptable for demo window
- **OIDC Test with Second Account**: Lower priority post-talk
