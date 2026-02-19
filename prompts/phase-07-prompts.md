# Phase 7: Production Hardening — Prompt Log

## Summary

- **Start time:** 2026-02-18 ~06:35 EST
- **End time:** 2026-02-18 ~06:55 EST (initial), ~12:05 EST (version bumps)
- **Total AI time:** 19 min (cert-manager 5 + quotas/PDBs 3 + docs 5 + gitleaks fix 3 + version bumps 3)
- **Correction prompts:** 2 (cert-manager subdirectory, gitleaks false positive) + 3 (Falco version bump)
- **Components:** TLS + cert-manager, Resource Quotas + PDBs, Documentation, OIDC (deferred)

*Note: Prompts reconstructed from git history, scorecard notes, and session data.*

---

## Prompt 1 (Phase 7, ~06:35)
**Type:** Initial
**Prompt:** Write Phase 7 tests (9 tests), then install cert-manager 1.19.x with HTTP-01 ClusterIssuers, ResourceQuota (10 pods, 4 CPU, 8Gi) in apps namespace, 5 PDBs for platform components.
**Result:** Partial — cert-manager Application in subdirectory not discovered
**Time spent:** 5 min
**Correction needed:** Yes — app-of-apps doesn't recurse into subdirectories

## Prompt 2 (Phase 7, ~06:40)
**Type:** Correction
**Prompt:** cert-manager Application not appearing in ArgoCD — YAML was in gitops/apps/cert-manager/ subdirectory.
**Result:** Success — moved to top-level gitops/apps/cert-manager.yaml
**Time spent:** 2 min
**Correction needed:** Also needed to add cert-manager namespace to namespaces.yaml and force refresh

## Prompt 3 (Phase 7, ~06:42)
**Type:** Initial
**Prompt:** Create SECURITY.md (8 sections), COST.md, ADR-007 auth strategy.
**Result:** Success — all correct first try
**Time spent:** 5 min
**Correction needed:** No

## Prompt 4 (Phase 7, ~06:47)
**Type:** Correction
**Prompt:** gitleaks found testpass123 in infrastructure/terraform/secrets.tf.
**Result:** Success — created .gitleaks.toml allowlist
**Time spent:** 3 min
**Correction needed:** Known test secret for ESO validation; allowlisted by commit + path

## Prompt 5 (Phase 7, ~11:55) — Version Audit
**Type:** Correction
**Prompt:** Bump cert-manager v1.19.1 → v1.19.3 and Falco chart 7.2.1 → 8.0.0.
**Result:** Partial — Falco needed 3 correction cycles for gRPC→HTTP migration
**Time spent:** 10 min total
**Correction needed:** Yes — gRPC deprecated, wrong service name, chart template override

## Test Results
- 59 tests passing after Phase 7
- Commits: `0cd2c93` through `be64113` (6 commits including version bumps)
