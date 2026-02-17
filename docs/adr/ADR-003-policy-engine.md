# ADR-003: Policy Engine — Kyverno 1.17+

## Status

Accepted

## Context

The IDP needs admission-time policy enforcement to prevent non-compliant
workloads from running. Policies must enforce resource limits, registry
restrictions, privilege escalation prevention, and labeling standards.

Enforcement must be scoped to the `apps` namespace only — system namespaces
(kube-system, argocd, monitoring, kyverno itself) must be excluded to prevent
policies from breaking platform components.

## Decision

Use Kyverno 1.17+ with traditional ClusterPolicy resources in enforce mode,
scoped exclusively to the `apps` namespace via `match.namespaces`.

Key design choices:
- **Namespace targeting:** Allowlist approach (`match.namespaces: [apps]`) instead
  of denylist (`exclude`) — safer, new namespaces aren't exposed by default
- **Policy syntax:** Traditional `validate/pattern` (not CEL) for broader audience
  familiarity at the conference. CEL policies are stable in 1.17+ but optional.
- **Webhook exclusions:** kyverno and kube-system excluded from webhooks to
  prevent deadlock on restart
- **PSS complement:** Pod Security Standards labels on `apps` provide
  defense-in-depth alongside Kyverno

Policies deployed:
1. `require-labels` — app and version labels required
2. `restrict-image-registries` — only ghcr.io, docker.io/library, ECR allowed
3. `require-resource-limits` — CPU and memory limits required
4. `disallow-privileged` — no privileged containers
5. `require-probes` — readiness and liveness probes required
6. `require-networkpolicy` — audit-mode check for NetworkPolicy existence

## Consequences

**Positive:**
- Native K8s CRDs, no Rego learning curve
- Clear allowlist scoping prevents accidental system namespace enforcement
- Rich policy report generation for compliance dashboards

**Negative:**
- Must test every policy against all system namespace workloads before deploy
- Traditional ClusterPolicy is deprecated in favor of CEL (still works in 1.17,
  removal planned in future version)

## Alternatives Considered

**OPA/Gatekeeper (CNCF Graduated):** Powerful constraint framework using Rego.
Steeper learning curve. More mature but less Kubernetes-native.

**Kubewarden (CNCF Sandbox):** Policy-as-code with WebAssembly. Newer, smaller
community. Interesting technology but less battle-tested.
