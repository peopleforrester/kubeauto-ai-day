# Phase 1: Foundation — Prompt Log

## Summary

- **Start time:** 2026-02-17 ~13:30 EST
- **End time:** 2026-02-17 ~14:00 EST
- **Total AI time:** 37 min (VPC 5 + EKS 25 + IAM 5 + NS 2)
- **Correction prompts:** 5 (EKS 3, IAM 1, VPC 1)
- **Components:** VPC + Networking, EKS Cluster, IAM Roles + Pod Identity, Namespace Structure

*Note: Prompts reconstructed from git history, scorecard notes, and session data.*

---

## Prompt 1 (Phase 1, ~13:30)
**Type:** Initial
**Prompt:** Write Phase 1 tests, then implement EKS cluster with VPC, IAM, namespaces using Terraform.
**Result:** Partial — VPC and namespace structure correct; EKS module used v20 variable names
**Time spent:** 5 min (VPC portion)
**Correction needed:** Yes (EKS portion)
**Notes:** VPC module config straightforward; NAT gateway + subnet tagging correct first try. PSS labels on apps namespace correct.

## Prompt 2 (Phase 1, ~13:35)
**Type:** Correction
**Prompt:** Terraform plan fails — EKS module v21 doesn't have `cluster_name` or `cluster_version` variables.
**Result:** Success after fix
**Time spent:** 8 min
**Correction needed:** Fixed variable renames (name, kubernetes_version)
**Notes:** Module v21.15 renamed variables from v20. Second correction needed for AWS provider 6.x dependency.

## Prompt 3 (Phase 1, ~13:43)
**Type:** Correction
**Prompt:** Addon bootstrap timing — VPC CNI and CoreDNS addons appear stuck during first terraform apply.
**Result:** Success (patience, not a code fix)
**Time spent:** 12 min (waiting)
**Correction needed:** No code change — addons install after cluster Ready
**Notes:** Chicken-and-egg: cluster needs CNI to schedule pods, but CNI addon installs after cluster exists. Terraform handles via implicit deps.

## Prompt 4 (Phase 1, ~13:55)
**Type:** Initial
**Prompt:** Configure IAM roles for EBS CSI and AWS LB Controller.
**Result:** Success with one correction
**Time spent:** 5 min
**Correction needed:** Used IRSA instead of Pod Identity for both (better addon support)
**Notes:** IRSA roles correct; Helm release for LB Controller wired properly with serviceAccount annotations.

## Test Results
- 10 tests passing after Phase 1
- Committed: `2a60554` (2026-02-17 13:54)
