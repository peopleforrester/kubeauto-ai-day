# Phase 3: Security Stack — Prompt Log

## Summary

- **Start time:** 2026-02-17 ~14:35 EST
- **End time:** 2026-02-17 ~17:10 EST
- **Total AI time:** 45 min (Kyverno 22 + Falco 15 + ESO 12 + RBAC 3 + NetPol 3)
- **Correction prompts:** 8 (Kyverno 3, Falco 3, ESO 2)
- **Components:** Kyverno Install, Kyverno Policies, Kyverno Interactions, Falco Install, Falco Custom Rules, ESO + Secrets Manager, RBAC, NetworkPolicies

*Note: Prompts reconstructed from git history, scorecard notes, and session data.*

---

## Prompt 1 (Phase 3, ~14:35)
**Type:** Initial
**Prompt:** Write Phase 3 security tests, then install Kyverno 1.17 with 6 ClusterPolicies.
**Result:** Partial — webhook config format wrong for chart 3.7.0
**Time spent:** 15 min
**Correction needed:** Yes — 3 cycles

## Prompt 2 (Phase 3, ~14:50)
**Type:** Correction
**Prompt:** Kyverno webhook failing — namespaceSelector format is list but chart expects map.
**Result:** Partial — config fixed but CRDs too large for client-side apply
**Time spent:** 5 min
**Correction needed:** Yes — needed ServerSideApply=true

## Prompt 3 (Phase 3, ~14:55)
**Type:** Correction
**Prompt:** Kyverno CRDs fail apply — annotation too large (256KB limit).
**Result:** Partial — ServerSideApply added but ArgoCD cache stale
**Time spent:** 2 min
**Correction needed:** Yes — needed hard refresh

## Prompt 4 (Phase 3, ~14:57)
**Type:** Initial
**Prompt:** Deploy 6 Kyverno ClusterPolicies with enforce mode in apps namespace only.
**Result:** Success — all 6 policies correct first try
**Time spent:** 5 min (policies) + 2 min (interaction testing)
**Correction needed:** No
**Notes:** Pod rejection via dry-run works; no false positives in system namespaces.

## Prompt 5 (Phase 3, ~16:30)
**Type:** Initial
**Prompt:** Install Falco with eBPF driver and 5 custom rules (3 general + 2 EKS-aware).
**Result:** Partial — skill file had wrong chart version (4.x vs 7.x)
**Time spent:** 10 min
**Correction needed:** Yes — 2 cycles

## Prompt 6 (Phase 3, ~16:40)
**Type:** Correction
**Prompt:** Falco rule "Write Below Etc" uses removed `write_etc_common` macro.
**Result:** Success after inline condition replacement
**Time spent:** 5 min
**Correction needed:** Replaced with inline evt.dir/fd.name conditions

## Prompt 7 (Phase 3, ~16:50)
**Type:** Initial
**Prompt:** Install ESO 1.3.2 with AWS Secrets Manager integration via IRSA.
**Result:** Partial — used v1beta1 API instead of v1
**Time spent:** 12 min
**Correction needed:** Yes — 2 cycles (API version + ArgoCD cache stale)

## Prompt 8 (Phase 3, ~17:00)
**Type:** Initial
**Prompt:** Add RBAC roles and NetworkPolicies for namespace isolation.
**Result:** Success — both correct first try
**Time spent:** 6 min total
**Correction needed:** No
**Notes:** Default deny + DNS allow + ingress allow pattern well-understood.

## Test Results
- 27 tests passing after Phase 3
- Commits: `44e6ed6` through `cb52d78` (8 commits, one per logical component)
