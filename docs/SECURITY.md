# ABOUTME: Security posture documentation for the KubeAuto Day IDP.
# ABOUTME: Covers all 8 security domains with configuration details and rationale.

# Security Posture

This document describes the security controls implemented in the KubeAuto Day
Internal Developer Platform running on Amazon EKS.

## 1. Kyverno Policy Summary

**Engine:** Kyverno 1.17+ (ClusterPolicy)
**Mode:** Enforce in `apps` namespace only; all system namespaces excluded

| Policy | Type | Description |
|--------|------|-------------|
| `require-resource-limits` | Validate | All containers must have CPU/memory requests and limits |
| `require-probes` | Validate | All containers must have readiness and liveness probes |
| `disallow-latest-tag` | Validate | Image tags must not be `latest` |
| `disallow-privilege-escalation` | Validate | `allowPrivilegeEscalation` must be false |
| `require-run-as-non-root` | Validate | `runAsNonRoot` must be true, capabilities drop ALL |
| `require-labels` | Validate | Pods must have `app` and `version` labels |

**Excluded namespaces:** kube-system, kube-public, kube-node-lease, argocd,
monitoring, security, platform, backstage, cert-manager.

## 2. Falco Rules Summary

**Engine:** Falco (CNCF Graduated), eBPF driver
**Deployment:** DaemonSet in `security` namespace

**Default rules (enabled):**
- Terminal shell in container
- Write below /etc
- Read sensitive file untrusted
- Contact K8s API from container

**Custom rules (5 total):**
- Write Below Etc in Container (Warning)
- Sensitive File Read in Container (Critical)
- Crypto Mining Detection (Critical)
- Container Accessing EC2 Metadata (Critical) — EKS-specific
- Pod Exec in Sensitive Namespace (Warning) — EKS-specific

**Output:** JSON logs + Falcosidekick with Prometheus metrics exporter.

## 3. RBAC Model

**Principle:** Least-privilege, namespace-scoped role bindings.

| Role | Scope | Permissions |
|------|-------|-------------|
| `platform-admin` | ClusterRole | Full access to platform namespaces |
| `developer-view` | ClusterRole | Read-only across all namespaces |
| `apps-deployer` | Role (apps) | Create/update deployments, services, configmaps |

**Cross-namespace isolation:** Verified by test — `developer-view` cannot create
resources outside their bound namespace.

**ArgoCD RBAC:** OIDC users mapped to read-only role (view applications, no
sync/delete). Admin users retain full access via local admin account.

## 4. NetworkPolicy Model

**Strategy:** Default-deny with explicit allow rules per namespace.

**`apps` namespace policies:**
| Policy | Direction | Allows |
|--------|-----------|--------|
| `default-deny-all` | Ingress + Egress | Nothing (baseline) |
| `allow-dns` | Egress | UDP/TCP 53 to kube-system (CoreDNS) |
| `allow-ingress-controller` | Ingress | From kube-system on ports 8080, 5000 |

**Result:** Pods in `apps` can resolve DNS but cannot initiate outbound
connections or receive traffic from other application pods. Only the AWS
Load Balancer Controller in kube-system can reach application services.

## 5. ESO Secret Flow

**Stack:** External Secrets Operator 1.3.2 → AWS Secrets Manager

```
AWS Secrets Manager          ESO ClusterSecretStore       ExternalSecret        K8s Secret
┌────────────────┐          ┌────────────────────┐      ┌───────────────┐     ┌──────────┐
│ kubeauto/       │  ←IRSA── │ aws-secretsmanager │ ──── │ apps/test-   │ ──── │ synced   │
│ test-secret    │          │ (platform NS)      │      │ secret       │     │ secret   │
└────────────────┘          └────────────────────┘      └───────────────┘     └──────────┘
```

**Authentication:** IRSA (IAM Roles for Service Accounts) via Pod Identity
fallback. The ESO service account assumes an IAM role with
`secretsmanager:GetSecretValue` scoped to `kubeauto/*` resources.

**No secrets in Git.** Only ExternalSecret references (secret name, key path)
are stored in the repository. The actual secret values are resolved at runtime.

## 6. TLS Posture

**Stack:** cert-manager 1.19+ with Let's Encrypt ACME

**ClusterIssuers:**
| Issuer | Server | Purpose |
|--------|--------|---------|
| `letsencrypt-staging` | LE Staging | Initial testing, avoids rate limits |
| `letsencrypt-production` | LE Production | Production certificates |

**Challenge type:** HTTP-01 via ALB ingress. Works with any DNS provider —
no Route53 dependency.

**Coverage:** TLS on all externally-facing ingresses (ArgoCD, Backstage,
Grafana, sample app) once domain DNS is configured.

## 7. OIDC Configuration

**Provider:** GitHub OAuth App
**Flow:** GitHub → OAuth callback → ArgoCD/Backstage/Grafana session

| Service | Auth Config |
|---------|-------------|
| ArgoCD | Dex connector with GitHub OIDC, RBAC mapping to read-only |
| Backstage | GitHub auth provider in app-config.yaml |
| Grafana | GitHub OAuth in grafana.ini |

**Credential storage:** OAuth client_id and client_secret stored in AWS
Secrets Manager (`kubeauto/github-oauth`), synced via ESO.

## 8. Audit Trail

**Falco alerts:** Real-time syscall monitoring with JSON output. All events
include pod name, namespace, container image, and user context.

**Kyverno policy reports:** ClusterPolicyReports generated for all policy
evaluations. Available via `kubectl get clusterpolicyreport`.

**ArgoCD audit log:** All sync operations, application changes, and RBAC
decisions logged to ArgoCD server pods.

**Prometheus alerting:** 4 custom PrometheusRules fire for:
- NodeNotReady (Critical, 5m threshold)
- PodCrashLoop (Warning, 3 restart threshold)
- ArgoCDAppDegraded (Warning, 5m threshold)
- FalcoCriticalAlert (Critical, immediate)

**Grafana dashboards:** Platform Overview dashboard with 8 panels covering
cluster health, security events, and component status.
