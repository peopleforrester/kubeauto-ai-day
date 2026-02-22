# Remaining Items — KubeAuto Day IDP

Last updated: 2026-02-22

## Status: Platform Complete, Presentation Prep In Progress

All 7 build phases are done. 27/27 components scored. 59 tests passing.
Cluster is live. Collateral (blog, slides outline, social, QR codes) committed.

---

## Must Do Before March 23

### 1. Build Actual Slides
- Source: `collateral/slide-outline.md` (19 slides, ~27 min)
- Format: PowerPoint or Google Slides
- Owner: Michael (manual task)

### 2. Demo Runbook 3x End-to-End
- Source: `collateral/demo-runbook.md`
- Run the full demo flow 3 times without intervention
- Capture screenshot fallbacks for each demo step
- Owner: Michael (manual task)

### 3. Practice Run with Timer
- Target: 27 minutes for 30-minute slot
- Include demo transitions and slide pacing
- Owner: Michael (manual task)

### 4. Fix test1 DNS (Negative Cache)
- Issue: `test1.ai-enhanced-devops.com` returns NXDOMAIN despite wildcard
- Root cause: Negative DNS cache (SOA shows 3601s negative TTL)
- Fix: Add explicit CNAME record in Namecheap for `test1`
- Owner: Michael (Namecheap admin panel)

---

## Should Do

### 5. Screenshot Fallbacks for Live Demo
- Capture screenshots of: ArgoCD dashboard, Grafana dashboard, Backstage catalog,
  Unicorn Party app, E-Commerce Frontend
- Store in `collateral/screenshots/` for slide deck fallbacks
- Status: Tracking, not yet captured

### 6. OIDC Test with Second GitHub Account
- Verify GitHub OIDC login with a non-admin account (WiggityWhitney)
- Confirm RBAC scoping works as expected
- Owner: Michael (manual task)

---

## Nice to Have (Not Required)

### ~~7. Eight Guardrails Reconciliation~~ DONE (2026-02-22)
- All three layers implemented: Layer 1 (`.pre-commit-config.yaml`, git hooks),
  Layer 2 (`.claude/settings.json`, Claude Code hooks), Layer 3 (Kyverno, Falco, etc.)
- Standalone docs: `docs/EIGHT-GUARDRAILS.md`, `docs/EIGHT-GUARDRAILS-RECONCILIATION.md`
- All 6 skill files updated with "Guardrail Integration" sections
- `docs/SECURITY.md` cross-referenced with guardrail numbers

### 8. Make Repo Public
- Currently private. Decision pending on timing.
- Pre-publish checklist: run `/gh-public-check`, verify no secrets, confirm
  `.gitignore` coverage, remove any private references

### ~~9. Git Tags for Phase Completion~~ DONE (2026-02-22)
- 8 annotated tags created: `phase-0-complete` through `phase-7-complete`
- Each tag points to the final commit for that phase with descriptive message

### ~~10. Guardrail Column in Scorecard~~ DONE (2026-02-22)
- Added "Guardrails" column to `spec/SCORECARD.md` mapping each component to guardrails #1-#8
- Added Guardrail Coverage summary table showing which components implement each guardrail

---

## Decided: Not Doing

- **GitHub Actions CI**: Credit-limited for the month, skip
- **Blog/social publishing**: Content exists, Michael handles scheduling
- **Known quirks** (ArgoCD app-of-apps OutOfSync, Kyverno CRD OutOfSync):
  Architectural characteristics, not bugs. No fix needed.
- **Cluster cost optimization**: Aware of $0.57/hr, acceptable for demo window
