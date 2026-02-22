# Backstage

Developer portal providing a service catalog and self-service templates.
Deployed via ArgoCD using the Backstage Helm chart 2.6.3.

## Directory Structure

```
catalog/
  catalog-info.yaml              # Root catalog file (System + Component refs)
  systems/
    sample-app.yaml              # System entity for the sample Flask app

templates/
  deploy-service/
    template.yaml                # Self-service template: deploy a new service
    skeleton/
      deployment.yaml            # Kyverno-compliant Deployment scaffold
      service.yaml               # Service scaffold
  create-namespace/
    template.yaml                # Self-service template: create a namespace
    skeleton/
      namespace.yaml             # Namespace scaffold with PSS labels

k8s/
  backstage-rbac.yaml            # RBAC for Backstage's K8s plugin
  catalog-configmap.yaml         # ConfigMap mounting catalog files into Backstage
  templated-test-svc.yaml        # Test service created from deploy-service template
```

## Catalog Architecture

Backstage uses a static file catalog approach (no external providers):

1. Catalog YAML files are committed to this repo
2. A ConfigMap mounts them into the Backstage pod
3. Backstage reads the ConfigMap on startup

This avoids needing GitHub App credentials for catalog discovery.

## Software Templates

Templates produce Kyverno-compliant resources:
- Required labels (`app.kubernetes.io/name`, `app.kubernetes.io/version`)
- Resource limits (CPU + memory)
- Liveness and readiness probes
- Targeted to the `apps` namespace

## Authentication

GitHub OAuth for user login. See [ADR-007](../docs/adr/ADR-007-auth-strategy.md).

## Adding Catalog Entities

1. Create a YAML entity in `catalog/` following the
   [Backstage descriptor format](https://backstage.io/docs/features/software-catalog/descriptor-format)
2. Reference it from `catalog/catalog-info.yaml`
3. Update the ConfigMap in `k8s/catalog-configmap.yaml`
4. Commit and push — ArgoCD deploys, Backstage picks up on next refresh

See [ADR-006](../docs/adr/ADR-006-developer-portal.md) for Backstage selection rationale.
