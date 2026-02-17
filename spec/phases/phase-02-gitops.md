# Phase 2: GitOps Bootstrap (Budget: 90 min)

**Goal:** ArgoCD installed, app-of-apps pattern bootstrapped, all subsequent components deployed via GitOps.

**Inputs:** Working EKS cluster from Phase 1.

**Outputs:**
- ArgoCD 3.2+ installed in argocd namespace via Helm
- ArgoCD configured with SSO disabled (initial), admin password set via Secret
- App-of-apps root Application pointing to gitops/bootstrap/
- ApplicationSets for environment promotion (dev only initially)
- ArgoCD RBAC configured with project-scoped access
- Every subsequent component deployed as an ArgoCD Application (no more kubectl apply)

**Test Criteria (tests/test_phase_02_gitops.py):**
- ArgoCD server pod is Running
- ArgoCD UI is accessible (port-forward or ingress)
- Root app-of-apps Application exists and is Synced/Healthy
- At least the namespace Application is Synced
- No Degraded apps
- ArgoCD can detect drift (manually change a resource, verify OutOfSync)
- Git repo is the single source of truth

**Completion Promise:** `<promise>PHASE2_DONE</promise>`

**Known Risk:** ArgoCD sync waves and resource ordering. The app-of-apps needs sync waves: namespaces first, then CRDs, then apps.

**Key Technology Decisions:**
- ArgoCD: 3.2+ (2.x is EOL; annotation-based tracking default)
- RBAC subject format changed for Dex/OIDC in 3.x
- Demo sync interval: 30s (set in Phase 6)

**ADR:** ADR-002 (GitOps Engine: ArgoCD)
**Commits:** 2 (ArgoCD install; App-of-apps + RBAC)
