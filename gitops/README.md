# GitOps

ArgoCD-managed Kubernetes resources using the app-of-apps pattern.

## Directory Structure

```
bootstrap/
  app-of-apps.yaml      # Root Application that manages all child apps

apps/                    # 26 ArgoCD Application manifests
  namespaces.yaml        # Namespace definitions (sync-wave: -10)
  kyverno.yaml           # Policy engine
  kyverno-policies.yaml  # 6 ClusterPolicies
  falco.yaml             # Runtime security
  falcosidekick.yaml     # Falco event forwarding
  external-secrets.yaml  # ESO operator
  eso-resources.yaml     # ClusterSecretStore + ExternalSecrets
  rbac.yaml              # ClusterRoles + RoleBindings
  network-policies.yaml  # Default-deny + allow rules
  prometheus.yaml        # kube-prometheus-stack (Prometheus + Grafana)
  otel-collector.yaml    # OpenTelemetry Collector
  grafana-dashboards.yaml  # Platform Overview dashboard
  tempo.yaml             # Distributed tracing
  loki.yaml              # Log aggregation
  promtail.yaml          # Log shipping
  sample-app.yaml        # Flask demo app
  backstage.yaml         # Developer portal
  backstage-resources.yaml # Backstage RBAC + catalog ConfigMap
  cert-manager.yaml      # TLS certificate management
  cert-manager-issuers.yaml # Let's Encrypt ClusterIssuers
  resource-quotas.yaml   # ResourceQuota + PDBs
  unicorn-party.yaml     # Demo app (interactive)
  ecom-frontend.yaml     # Demo app (e-commerce)
  ecom-api.yaml          # Demo app (e-commerce API)
  ecom-worker.yaml       # Demo app (e-commerce worker)
  load-generator.yaml    # Traffic generation for observability

argocd/
  values.yaml            # ArgoCD Helm chart values

manifests/               # Raw Kubernetes manifests for demo apps
  unicorn-party/         # Deployment, Service, Ingress
  ecom-frontend/         # Deployment, Service, Ingress
  ecom-api/              # Deployment, Service
  ecom-worker/           # Deployment, Service
  load-generator/        # Deployment

namespaces/
  namespaces.yaml        # Namespace definitions with PSS labels
```

## App-of-Apps Pattern

The root `bootstrap/app-of-apps.yaml` is applied once manually:

```bash
kubectl apply -f gitops/bootstrap/app-of-apps.yaml
```

After this, ArgoCD manages everything. No more `kubectl apply` is needed.

The root app watches `gitops/apps/` and creates child Applications for each YAML file.
Each child app points to either a Helm chart (external) or a directory in this repo.

## Sync Wave Ordering

Negative waves are infrastructure prerequisites. Positive waves are applications.
Gaps between groups are reserved for future components.

| Wave | Resources |
|------|-----------|
| -10  | Namespaces |
| -5   | Kyverno (CRD provider) |
| -4   | Kyverno policies, RBAC, NetworkPolicies, ESO operator |
| -3   | Falco, ESO resources (ClusterSecretStore + ExternalSecrets) |
| -2   | Falcosidekick |
| 1    | Prometheus (kube-prometheus-stack), cert-manager |
| 2    | OTel Collector, cert-manager ClusterIssuers |
| 3    | Grafana dashboards, resource quotas, Loki, Tempo |
| 4    | Promtail |
| 5    | Sample app, Backstage resources (RBAC, catalog) |
| 6    | Backstage |
| 7    | Demo apps (Unicorn Party, E-commerce frontend/API/worker) |
| 8    | Load generator |

## Adding a New Application

1. Create the Kubernetes manifests or identify the Helm chart
2. Create a new `gitops/apps/<name>.yaml` ArgoCD Application manifest
3. Set the appropriate sync wave annotation
4. Commit and push — ArgoCD will detect and deploy within 30 seconds

See [ADR-002](../docs/adr/ADR-002-gitops-engine.md) for the ArgoCD selection rationale.
