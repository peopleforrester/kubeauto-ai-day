# Version Map — Chart ↔ Application ↔ Breaking Changes

All Helm-deployed components with their chart version, application version,
and notable breaking changes between recent versions.

Last updated: February 2026

---

## Deployed Versions

| Component | Helm Chart | Chart Version | App Version | Repository |
|-----------|-----------|---------------|-------------|-----------|
| ArgoCD | argo-cd | 9.4.2 | 3.3.0 | `https://argoproj.github.io/argo-helm` |
| Kyverno | kyverno | 3.7.0 | 1.17.0 | `https://kyverno.github.io/kyverno` |
| Falco | falco | 8.0.0 | 0.43.0 | `https://falcosecurity.github.io/charts` |
| Falcosidekick | falcosidekick | 0.12.1 | (latest) | `https://falcosecurity.github.io/charts` |
| ESO | external-secrets | 1.3.2 | 1.3.2 | `https://charts.external-secrets.io` |
| kube-prometheus-stack | kube-prometheus-stack | 82.1.0 | Prom 3.9.1 / Grafana 12.3.3 | `https://prometheus-community.github.io/helm-charts` |
| OTel Collector | opentelemetry-collector | 0.145.0 | 0.145.0 | `https://open-telemetry.github.io/opentelemetry-helm-charts` |
| Backstage | backstage | 2.6.3 | 1.9.1 | `https://backstage.github.io/charts` |
| cert-manager | cert-manager | v1.19.3 | 1.19.3 | `https://charts.jetstack.io` |
| AWS LB Controller | aws-load-balancer-controller | 1.11.0 | 2.x | `https://aws.github.io/eks-charts` |

## Terraform Modules

| Module | Version | Source |
|--------|---------|--------|
| EKS | ~> 21.0 (21.15.x) | `terraform-aws-modules/eks/aws` |
| VPC | ~> 5.0 | `terraform-aws-modules/vpc/aws` |
| IAM (IRSA) | ~> 5.0 | `terraform-aws-modules/iam/aws` |
| AWS Provider | ~> 6.0 | `hashicorp/aws` |
| Helm Provider | ~> 2.0 | `hashicorp/helm` |

## Infrastructure

| Component | Version | Notes |
|-----------|---------|-------|
| EKS | 1.34 | Standard support (not extended) |
| Instance type | m7i.xlarge | Current-gen Intel, 4 vCPU, 16 GiB |
| Node count | 2 (min 2, max 4) | Managed node group, AL2023 AMI |
| Region | us-west-2 | |
| VPC CIDR | 10.0.0.0/16 | 3 AZs, single NAT gateway |

---

## Breaking Changes Reference

### ArgoCD: chart 7.x → 9.x (ArgoCD 2.x → 3.2)

**The entire ArgoCD 2.x line is EOL.** Chart 5.x and 6.x = ArgoCD 2.x.
Chart 7.x = ArgoCD 3.0. Chart 9.x = ArgoCD 3.2–3.3.

| Change | Impact |
|--------|--------|
| Default tracking: label → annotation | Resources tracked via `argocd.argoproj.io/tracking-id` annotation, not labels |
| RBAC subject format changed | SSO subjects now use `oidc:` prefix (e.g., `oidc:my-group`) |
| Fine-grained RBAC no longer applies to sub-resources | Simplifies RBAC but may break existing policies |
| Deprecated metrics removed | Monitoring dashboards targeting old metric names will break |
| `argocd-cm` keys moved to `configs.params` | Helm values structure changed; raw ConfigMap manipulation no longer works |

### Kyverno: chart 3.5 → 3.7.0 (Kyverno 1.12 → 1.17)

| Change | Impact |
|--------|--------|
| CEL policies promoted to v1 stable | Traditional `ClusterPolicy` still works but is deprecated direction |
| Webhook config structure changed | `config.webhooks.namespaceSelector` (map), not list of webhooks |
| CRDs exceed annotation limit | Requires `ServerSideApply=true` in ArgoCD syncOptions |

### Falco: chart 7.x → 8.0.0 (Falco 0.42 → 0.43)

| Change | Impact |
|--------|--------|
| gRPC output deprecated | Must use `falco.http_output` instead of `falco.grpc_output` |
| `write_etc_common` macro removed | Custom rules using this macro fail silently; use inline conditions |
| Chart template computes Falcosidekick URL | Manual `http_output.url` is overridden; use `falcosidekick.fullfqdn` |
| `modern_ebpf` is now sole default | `ebpf` (classic) and `module` are deprecated |

### ESO: 0.x → 1.3.2

| Change | Impact |
|--------|--------|
| API version v1beta1 → v1 | All ExternalSecret and ClusterSecretStore manifests must use `v1` |
| Provider config structure | Some provider fields renamed in v1 API |

### OTel Collector: chart 0.89 → 0.145

| Change | Impact |
|--------|--------|
| `image.repository` no longer defaulted | Must explicitly set to `otel/opentelemetry-collector-contrib` |
| `k8s` image lacks most exporters | Only `contrib` image has `prometheusremotewrite` exporter |
| DaemonSet mode: no ClusterIP service | Must set `service.enabled: true` explicitly |

### Terraform EKS module: v20 → v21

| Change | Impact |
|--------|--------|
| `aws-auth` sub-module removed entirely | Use API authentication mode (`authentication_mode = "API"`) |
| `cluster_name` → `name` | Variable renamed |
| `cluster_version` → `kubernetes_version` | Variable renamed |
| `platform` variable removed | Use `ami_type` instead |
| Default auth mode: ConfigMap → API | No more aws-auth ConfigMap management |

### Backstage: 1.30 → 1.46+

| Change | Impact |
|--------|--------|
| Legacy backend system removed | Must use `createBackend()` API; all pre-2024 tutorials are wrong |
| Plugin wiring changed | No more manual `packages/backend/src/index.ts` wiring |
| Catalog format stable | `catalog-info.yaml` format unchanged |

### cert-manager: v1.19.1 → v1.19.3

| Change | Impact |
|--------|--------|
| Patch release only | Bug fixes, no breaking changes |
| CRD install via `crds.enabled: true` | Stable approach; `installCRDs` is deprecated alias |

---

## Version Audit History

**Audit date: February 18, 2026**

Found 2 stale versions in deployed components:
1. cert-manager v1.19.1 → bumped to v1.19.3
2. Falco chart 7.2.1 (0.42.1) → bumped to chart 8.0.0 (0.43.0)

**Original spec audit date: February 11, 2026**

Found 6 critical version issues in planning documents:
1. ArgoCD 2.13+ → corrected to 3.2+ (2.x entirely EOL)
2. EKS 1.31 → corrected to 1.34 (1.31 in extended support at 6x cost)
3. Falco listed as "CNCF Sandbox" → corrected to "CNCF Graduated"
4. Crossplane listed as "CNCF Incubating 1.17" → corrected to "CNCF Graduated 2.1+"
5. Backstage 1.30+ → corrected to 1.46+ (legacy backend removed)
6. Terraform EKS module unpinned → pinned to ~> 21.0

All corrections applied to spec.md, PLAN.md, PRD.md, and CLAUDE.md before
build started.
