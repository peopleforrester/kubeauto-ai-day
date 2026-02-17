# ADR-002: GitOps Engine — ArgoCD 3.2+

## Status

Accepted

## Context

The IDP requires a GitOps engine to manage all Kubernetes resources after initial
bootstrap. The engine must support Helm charts, raw YAML, app-of-apps patterns,
and provide a visual UI for the KubeAuto Day demo.

ArgoCD 2.x is entirely end-of-life. ArgoCD 3.0 EOL'd on Feb 2, 2026. The current
stable line is 3.2+, which introduces breaking changes from 2.x that affect
resource tracking, RBAC subject format, and Helm chart versions.

## Decision

Use ArgoCD 3.2+ installed via Helm chart version 7.x (`argo-cd` from
`https://argoproj.github.io/argo-helm`).

Key configuration:
- **Resource tracking:** Annotation-based (default in 3.x, replaces label-based)
- **RBAC subjects:** Use `oidc:<group>` prefix format (3.x format)
- **Reconciliation:** 30s for demo (default 180s)
- **Self-heal:** Enabled on all applications
- **App-of-apps:** Root Application in `gitops/bootstrap/` manages child apps
  in `gitops/apps/` via sync waves
- **Sync waves:** -10 (namespaces) → -5 (security) → 0 (observability) →
  3 (platform) → 5 (workloads)

## Consequences

**Positive:**
- Strong visual UI for live demo — audience can see sync status in real-time
- Mature app-of-apps pattern for bootstrapping entire platform
- Native Helm support with values overrides
- Annotation-based tracking avoids label length limits

**Negative:**
- Sync wave ordering adds complexity; misconfigured waves cause cascading failures
- Most existing tutorials reference 2.x patterns (chart 5.x/6.x, label tracking,
  old RBAC format) — must actively avoid outdated patterns
- Initial install is kubectl (chicken-and-egg: can't use ArgoCD to install itself)

## Alternatives Considered

**Flux CD (CNCF Graduated):** Strong GitOps engine with native Kustomize support.
Lower market adoption (~11% vs ArgoCD's ~50%). No built-in web UI — would need
Weave GitOps or similar for the demo visual component.

**Raw kubectl + Kustomize:** Simplest approach, no additional tooling. No drift
detection, no self-heal, no visual UI. Not suitable for demonstrating GitOps
principles.

**Rancher Fleet:** Designed for multi-cluster. Overkill for single-cluster demo.
Less community adoption and documentation.
