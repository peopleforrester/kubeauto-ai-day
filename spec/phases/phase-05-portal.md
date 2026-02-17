# Phase 5: Developer Portal (Budget: 90 min)

**Goal:** Backstage running with service catalog, software templates that deploy through ArgoCD.

**Inputs:** Observable, secured cluster from Phase 4.

**Outputs:**
- Backstage 1.46+ installed via ArgoCD (new backend system, createBackend() API)
- Static file catalog locations (no GitHub token needed initially)
- Service catalog with sample app registered
- Software template: "Deploy a new service" (namespace, deployment, service, network policy, catalog-info.yaml, ArgoCD Application)
- Software template: "Create a new namespace" (namespace, RBAC, NetworkPolicy)

**Test Criteria (tests/test_phase_05_portal.py):**
- Backstage pod Running
- Backstage UI accessible
- Catalog has at least 1 component
- "Deploy a new service" template in template list
- Template execution creates ArgoCD Application
- ArgoCD syncs new app to Healthy
- New service pod Running
- New service passes all Kyverno policies

**Completion Promise:** `<promise>PHASE5_DONE</promise>`

**Known Risk:** Backstage plugin wiring is fragile. All pre-2024 tutorials outdated. ArgoCD plugin needs specific annotations.

**ADR:** ADR-006 (Developer Portal: Backstage)
**Commits:** 2 (Backstage install+catalog; Templates+wiring)
