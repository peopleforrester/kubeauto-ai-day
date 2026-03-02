# ABOUTME: Security posture documentation for the KubeAuto Day IDP.
# ABOUTME: Covers all 8 security domains with configuration details and rationale.

# Security Posture

This document describes the security controls implemented in the KubeAuto Day
Internal Developer Platform running on Amazon EKS.

All security controls map to the **Eight Guardrails Framework** documented in
[`docs/EIGHT-GUARDRAILS.md`](EIGHT-GUARDRAILS.md). Each section below notes
which guardrails it implements.

## 1. Kyverno Policy Summary — Guardrails #2, #3, #4, #8

**Engine:** Kyverno 1.17+ (ClusterPolicy)
**Mode:** Enforce in `apps` namespace only; all system namespaces excluded

| Policy | Type | Description |
|--------|------|-------------|
| `require-resource-limits` | Validate | All containers must have CPU/memory requests and limits |
| `require-probes` | Validate | All containers must have readiness and liveness probes |
| `restrict-image-registries` | Validate | Only allow images from approved registries |
| `disallow-privileged` | Validate | Privileged containers and privilege escalation blocked |
| `require-labels` | Validate | Pods must have `app` and `version` labels |
| `require-networkpolicy` | Audit | Namespaces must have at least one NetworkPolicy |

**Excluded namespaces:** kube-system, kube-public, kube-node-lease, argocd,
monitoring, security, platform, backstage, cert-manager.

## 2. Falco Rules Summary — Guardrails #3, #5

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

## 3. RBAC Model — Guardrail #2

**Principle:** Least-privilege, namespace-scoped role bindings.

| Role | Scope | Permissions |
|------|-------|-------------|
| `platform-admin` | ClusterRole | Full access to platform namespaces |
| `developer-view` | ClusterRole | Read-only across all namespaces |
| `apps-deployer` | Role (apps) | Create/update deployments, services, configmaps |

**Cross-namespace isolation:** Verified by test — `developer-view` cannot create
resources outside their bound namespace.

**ArgoCD RBAC:** Dex/GitHub OIDC users mapped via explicit RBAC bindings.
Default policy is deny-all — unapproved GitHub users who authenticate get zero
permissions. Named users (`peopleforrester`, `WiggityWhitney`) are mapped to
`platform-admin`. The `backstage` service account has `backstage-readonly` for
API access. Local admin account is disabled.

## 4. NetworkPolicy Model — Guardrail #2

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

## 5. ESO Secret Flow — Guardrail #7

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

## 6. TLS Posture — Guardrail #8

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

## 7. OIDC Configuration — Guardrail #1

**Provider:** GitHub OAuth Apps (separate apps per service for distinct callback URLs)
**Flow:** GitHub → OAuth callback → service-specific session

| Service | Auth Config | Access Control |
|---------|-------------|----------------|
| ArgoCD | Dex connector with GitHub OIDC | RBAC: deny-all default, explicit user→role bindings |
| Backstage | GitHub auth provider (`@backstage/plugin-auth-backend-module-github-provider`) | `usernameMatchingUserEntityName` resolver — only users with a matching `User` entity in the catalog can sign in |
| Grafana | GitHub OAuth in grafana.ini | OAuth app-level restriction |

### Backstage Auth Model

Backstage uses a two-gate authentication model:

1. **Gate 1 — GitHub OAuth**: Any GitHub user can initiate the OAuth flow
2. **Gate 2 — Sign-in Resolver**: After GitHub authenticates the user, the
   `usernameMatchingUserEntityName` resolver checks whether a `User` entity
   with a matching `metadata.name` exists in the Backstage catalog. If no
   match is found, sign-in is rejected.

**Adding users:** Create a `User` entity in `backstage/k8s/catalog-configmap.yaml`
with `metadata.name` matching the GitHub username (lowercase) and annotation
`github.com/user-login` matching the exact GitHub username.

**Permission framework:** Set to `allow-all-policy` (appropriate for demo).
All authenticated users have equal access within Backstage.

### ArgoCD Auth Model

ArgoCD uses Dex as an OIDC broker with GitHub as the identity provider:

1. **Authentication**: Any GitHub user can complete the OAuth flow via Dex
2. **Authorization**: RBAC policy determines access. Default policy is empty
   (deny-all), so unauthenticated users see nothing useful.

**Adding users:** Add `g, <github-username>, role:<role-name>` to
`configs.rbac.policy.csv` in `gitops/argocd/values.yaml`.

### Key Architectural Decisions

- **Custom Docker image required for Backstage auth**: The stock Backstage
  image (`ghcr.io/backstage/backstage`) uses the default `create-app` scaffold
  with guest-only `SignInPage`. The frontend `App.tsx` `providers` array is
  compiled into the Docker image at build time and cannot be changed via
  runtime config. Switching from guest to GitHub sign-in requires modifying
  `App.tsx`, rebuilding the image, and pushing to ECR.
- **ArgoCD admin disabled**: Admin account disabled via `admin.enabled: "false"`.
  GitHub OIDC is the only login method. The `argocd-initial-admin-secret` has
  been deleted.
- **Separate OAuth Apps**: ArgoCD and Backstage use different GitHub OAuth Apps
  because their callback URLs differ (`/api/dex/callback` vs
  `/api/auth/github/handler/frame`).

**Credential storage:** OAuth credentials stored in AWS Secrets Manager:
- `kubeauto/github-oauth` — ArgoCD GitHub OAuth (synced via ESO)
- `kubeauto/backstage-github-oauth` — Backstage GitHub OAuth (K8s secret)
- `kubeauto/argocd-backstage-token` — ArgoCD API token for Backstage plugin

## 8. Audit Trail — Guardrail #5

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
