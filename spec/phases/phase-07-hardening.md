# Phase 7: Production Hardening (Budget: 60 min)

**Goal:** OIDC authentication for attendee access, TLS everywhere, final security review.

**Inputs:** Integrated platform from Phase 6.

**Pre-Checklist:**
- Domain name decided and Route53 hosted zone ready
- GitHub OAuth App created
- OAuth client ID and secret stored in AWS Secrets Manager

**Outputs:**
- cert-manager 1.19+ with Let's Encrypt staging + production ClusterIssuers
- TLS on all ingresses (ArgoCD, Backstage, Grafana, sample app)
- GitHub OIDC for Backstage, Grafana, ArgoCD (read-only for OIDC users)
- Resource quotas on apps namespace (10 pods, 4 CPU, 8Gi)
- PDBs for ArgoCD, Prometheus, Grafana, Backstage
- docs/SECURITY.md (8 sections)
- docs/COST.md

**Test Criteria (tests/test_phase_07_hardening.py):**
- All ingresses have valid TLS
- HTTP redirects to HTTPS
- Backstage OIDC login works
- Grafana OIDC login works
- ArgoCD OIDC user can view but NOT sync/delete
- Resource quota enforced in apps
- PDBs exist for platform components
- No pods running as root
- No secrets in git (gitleaks scan)

**Completion Promise:** `<promise>PHASE7_DONE</promise>`

**ADR:** ADR-007 (Auth Strategy: GitHub OIDC)
**Commits:** 4 (TLS; OIDC; Quotas+PDBs; Audit+docs)
