# Phase 5: Developer Portal — Prompt Log

## Summary

- **Start time:** 2026-02-17 ~19:35 EST
- **End time:** 2026-02-17 ~19:55 EST
- **Total AI time:** 18 min (Backstage Install 10 + Templates 5 + Plugin Wiring 3)
- **Correction prompts:** 1 (Backstage Install)
- **Components:** Backstage Install, Software Templates, Backstage Plugin Wiring

*Note: Prompts reconstructed from git history, scorecard notes, and session data.*

---

## Prompt 1 (Phase 5, ~19:35)
**Type:** Initial
**Prompt:** Write Phase 5 tests, then deploy Backstage 1.9.1 (chart 2.6.3) with static catalog, 2 software templates (deploy-service, create-namespace), and sample app integration.
**Result:** Partial — 1 correction for Kyverno livenessProbe validation
**Time spent:** 10 min
**Correction needed:** Yes — dry-run test hit Kyverno's require-probes policy

## Prompt 2 (Phase 5, ~19:45)
**Type:** Correction
**Prompt:** Template skeleton test fails dry-run — Kyverno rejects pod without matching probe format.
**Result:** Success — ensured skeleton includes httpGet probes
**Time spent:** 2 min
**Correction needed:** Template skeleton updated

## Prompt 3 (Phase 5, ~19:47)
**Type:** Initial
**Prompt:** Configure Backstage catalog with static file locations via ConfigMap mount.
**Result:** Success — 4 catalog entities loaded (System, Component, 2 Templates)
**Time spent:** 3 min
**Correction needed:** No
**Notes:** Used ConfigMap-based catalog to avoid private GitHub repo auth. ArgoCD/K8s annotations on sample-app Component correct for plugin discovery.

## Prompt 4 (Phase 5, ~19:50)
**Type:** Initial
**Prompt:** Deploy sample Flask app with OTel auto-instrumentation and version label.
**Result:** Success — Kyverno-compliant, OTel traces flowing
**Time spent:** 5 min (across 2 commits)
**Correction needed:** No — added version label separately for Kyverno require-labels policy

## Test Results
- 43 tests passing after Phase 5
- Commits: `0b76776` through `8357c87` (4 commits)
