# Architecture Overview

## Platform Summary

This is a production-grade Internal Developer Platform (IDP) running on Amazon
EKS. It demonstrates the full stack that platform teams build and maintain:
GitOps, policy enforcement, runtime security, observability, secret management,
and a developer portal.

Everything after the initial Terraform apply is managed by ArgoCD. No kubectl
apply is used in production namespaces.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         AWS Account (us-west-2)                        │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    VPC (10.0.0.0/16)                              │  │
│  │                                                                    │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐                  │  │
│  │  │ Public AZ-a│  │ Public AZ-b│  │ Public AZ-c│  ← ALB          │  │
│  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘                  │  │
│  │        │NAT            │               │                          │  │
│  │  ┌─────┴──────┐  ┌─────┴──────┐  ┌─────┴──────┐                  │  │
│  │  │Private AZ-a│  │Private AZ-b│  │Private AZ-c│  ← Nodes        │  │
│  │  └────────────┘  └────────────┘  └────────────┘                  │  │
│  │                                                                    │  │
│  │  ┌──────────────────────────────────────────────────────────────┐ │  │
│  │  │                  EKS Cluster (v1.34)                         │ │  │
│  │  │                  2x m7i.xlarge nodes                         │ │  │
│  │  │                                                               │ │  │
│  │  │  Namespaces:                                                  │ │  │
│  │  │  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌───────────────┐  │ │  │
│  │  │  │  argocd  │ │ security │ │ monitoring│ │   backstage   │  │ │  │
│  │  │  │ ArgoCD   │ │ Kyverno  │ │ Prom+Graf │ │  Backstage    │  │ │  │
│  │  │  │ 3.2.6    │ │ Falco    │ │ OTel      │ │  1.9.1        │  │ │  │
│  │  │  │          │ │ ESO      │ │ Alerting  │ │  Templates    │  │ │  │
│  │  │  └──────────┘ └──────────┘ └───────────┘ └───────────────┘  │ │  │
│  │  │  ┌──────────┐ ┌──────────┐ ┌───────────────────────────────┐│ │  │
│  │  │  │   apps   │ │ platform │ │        cert-manager           ││ │  │
│  │  │  │ sample   │ │ quotas   │ │ TLS + ClusterIssuers          ││ │  │
│  │  │  │ app      │ │ PDBs     │ │ Let's Encrypt staging + prod  ││ │  │
│  │  │  └──────────┘ └──────────┘ └───────────────────────────────┘│ │  │
│  │  └──────────────────────────────────────────────────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌─────────────────┐  ┌──────────────────┐                             │
│  │ Secrets Manager  │  │ IAM (IRSA + Pod  │                             │
│  │ kubeauto/*       │  │ Identity)        │                             │
│  └─────────────────┘  └──────────────────┘                             │
└─────────────────────────────────────────────────────────────────────────┘

External:
┌──────────────┐     ┌──────────────────────────┐
│   GitHub     │────→│ ArgoCD polls every 30s   │
│ (GitOps src) │     │ for manifest changes     │
└──────────────┘     └──────────────────────────┘
```

## Component Flow

### GitOps Pipeline

```
Developer → git push → GitHub (staging branch)
                            │
                     ArgoCD polls (30s)
                            │
                     App-of-Apps root
                            │
            ┌───────────────┼───────────────┐
            │               │               │
      Sync Wave -10    Sync Wave -5    Sync Wave 0+
      (namespaces)     (CRDs/infra)    (applications)
```

ArgoCD manages 20 Applications via the app-of-apps pattern. Sync waves
ensure resources are created in dependency order:

| Wave | Components |
|------|-----------|
| -10 | Namespaces |
| -5 | Kyverno, cert-manager (CRD providers) |
| -3 | Falco, ESO (security infrastructure) |
| -1 | Falcosidekick, ESO resources |
| 0 | Prometheus, Grafana dashboards, RBAC, NetworkPolicies |
| 1 | OTel Collector, cert-manager issuers |
| 2 | Kyverno policies, resource quotas |
| 5 | Sample app, Backstage |

### Security Data Flow

```
Pod attempt → Kyverno admission webhook
                 │
            Policy check
            (6 ClusterPolicies)
                 │
         ┌───────┴────────┐
         │                 │
      Allowed           Denied
         │            (enforce in apps)
         │
    Runtime behavior → Falco eBPF
                          │
                    Falcosidekick
                          │
                    Prometheus metrics
                          │
                    Grafana dashboard
```

### Observability Data Flow

```
Application metrics ──→ Prometheus scrape
                             │
OTel Collector ──────────→ remote write
(host metrics, logs)         │
                        Prometheus TSDB
                             │
                        Grafana dashboards
                        Alert rules → AlertManager
```

### Secret Flow

```
AWS Secrets Manager
      │
ClusterSecretStore (IRSA auth)
      │
ExternalSecret (per namespace)
      │
Kubernetes Secret (auto-synced)
      │
Pod (mounted as env var or volume)
```

## Namespace Model

| Namespace | Purpose | Security | Policy Enforcement |
|-----------|---------|----------|--------------------|
| `argocd` | GitOps engine | System namespace, excluded from Kyverno | N/A |
| `security` | Falco, ESO, Kyverno, Falcosidekick | System namespace | N/A |
| `monitoring` | Prometheus, Grafana, OTel | System namespace | N/A |
| `backstage` | Developer portal | System namespace | N/A |
| `apps` | User workloads, sample app | **PSS baseline enforced**, Kyverno enforce mode | 6 ClusterPolicies enforced |
| `platform` | Resource quotas, PDBs, RBAC | System namespace | N/A |
| `cert-manager` | TLS certificate management | System namespace | N/A |
| `kube-system` | EKS system components | AWS managed | N/A |

The `apps` namespace has:
- Pod Security Standards `baseline` enforcement + `restricted` warnings
- Kyverno policies in enforce mode (all other namespaces excluded)
- Default-deny NetworkPolicy (egress limited to DNS only)
- ResourceQuota (10 pods, 4 CPU requests, 8Gi memory requests)

## Technology Choices

Each major decision is documented in an Architecture Decision Record:

| Decision | Choice | ADR |
|----------|--------|-----|
| Infrastructure as Code | Terraform + EKS module v21 | [ADR-001](adr/ADR-001-iac-tool.md) |
| GitOps engine | ArgoCD 3.2+ | [ADR-002](adr/ADR-002-gitops-engine.md) |
| Policy engine | Kyverno 1.17 (traditional ClusterPolicy) | [ADR-003](adr/ADR-003-policy-engine.md) |
| Runtime security | Falco 0.43 (eBPF driver) | [ADR-003b](adr/ADR-003b-runtime-security.md) |
| Secret management | ESO + AWS Secrets Manager | [ADR-004](adr/ADR-004-secret-management.md) |
| Observability | Prometheus + Grafana + OTel | [ADR-005](adr/ADR-005-observability-stack.md) |
| Developer portal | Backstage 1.9 | [ADR-006](adr/ADR-006-developer-portal.md) |
| Authentication | GitHub OIDC (via ArgoCD Dex) | [ADR-007](adr/ADR-007-auth-strategy.md) |

## Deployed Versions

| Component | Version | Chart | Installation Method |
|-----------|---------|-------|---------------------|
| EKS | 1.34 | N/A | Terraform |
| ArgoCD | 3.2.6 | argo-cd 9.x | Helm (Terraform bootstrap) |
| Kyverno | 1.17.0 | kyverno 3.7.0 | ArgoCD Application |
| Falco | 0.43.0 | falco 8.0.0 | ArgoCD Application |
| Falcosidekick | | falcosidekick 0.9.3 | ArgoCD Application |
| ESO | 1.3.2 | external-secrets 0.17.x | ArgoCD Application |
| Prometheus | 3.9.1 | kube-prometheus-stack 82.1.0 | ArgoCD Application |
| Grafana | 12.3.3 | (via kube-prometheus-stack) | ArgoCD Application |
| OTel Collector | 0.145.0 | opentelemetry-collector 0.145.0 | ArgoCD Application |
| Backstage | 1.9.1 | backstage 2.6.3 | ArgoCD Application |
| cert-manager | 1.19.3 | cert-manager v1.19.3 | ArgoCD Application |
| AWS LB Controller | 2.x | aws-load-balancer-controller 1.11.0 | Helm (Terraform) |

## What's In Scope

- Full EKS cluster lifecycle (Terraform create → ArgoCD manage → Terraform destroy)
- GitOps-only deployment (no kubectl apply after ArgoCD bootstrap)
- Policy enforcement on developer workloads
- Runtime threat detection via eBPF
- Secret management via AWS Secrets Manager
- Full observability stack (metrics, dashboards, alerts)
- Developer self-service via Backstage templates
- TLS certificate automation via Let's Encrypt

## What's Out of Scope

- Multi-cluster management
- Service mesh (Istio/Linkerd)
- CI/CD pipeline (GitHub Actions, Jenkins)
- Container registry scanning
- Backup and disaster recovery
- Cost optimization beyond instance selection
- Gateway API (used traditional Ingress + ALB)
- Crossplane (stretch goal, not implemented)
- Production OIDC (deferred — requires domain setup)
