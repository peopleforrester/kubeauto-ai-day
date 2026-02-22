# Backstage Templates — Skill File

## CRITICAL VERSION WARNING

**This project uses Backstage 1.46+.** The new backend system is **mandatory** since early 2025.

**ALL Backstage tutorials, blog posts, and Stack Overflow answers written before mid-2024 are WRONG.** They reference the legacy backend system which has been removed. Do NOT use any configuration patterns from:

- Old `packages/backend/src/index.ts` with manual `createServiceBuilder()` or plugin wiring
- `@backstage/backend-common` imports (deprecated package)
- `createRouter()` patterns for backend plugins
- Any tutorial showing `backend.add(plugin)` in a loop manually

The ONLY correct backend API is `createBackend()` from `@backstage/backend-defaults`.

---

## Correct Patterns

### Backend Entry Point (packages/backend/src/index.ts)

The new backend system uses auto-discovery. The backend entry point is minimal:

```typescript
// ABOUTME: Backstage backend entry point using new backend system (1.46+)
// ABOUTME: Uses createBackend() API with module auto-discovery

import { createBackend } from '@backstage/backend-defaults';

const backend = createBackend();

// Core services (auto-discovered from package.json)
backend.add(import('@backstage/plugin-app-backend/alpha'));
backend.add(import('@backstage/plugin-catalog-backend/alpha'));
backend.add(import('@backstage/plugin-scaffolder-backend/alpha'));
backend.add(import('@backstage/plugin-techdocs-backend/alpha'));
backend.add(import('@backstage/plugin-auth-backend'));
backend.add(import('@backstage/plugin-auth-backend-module-github-provider'));
backend.add(import('@backstage/plugin-proxy-backend/alpha'));
backend.add(import('@backstage/plugin-search-backend/alpha'));
backend.add(import('@backstage/plugin-search-backend-module-catalog/alpha'));

// ArgoCD plugin (community)
backend.add(import('@roadiehq/backstage-plugin-argo-cd-backend'));

// Kubernetes plugin
backend.add(import('@backstage/plugin-kubernetes-backend/alpha'));

backend.start();
```

### App Config — Catalog with Static File Locations (backstage/app-config.yaml)

For this project, use **static file catalog locations** initially. This avoids needing a GitHub token during the build phase.

```yaml
# ABOUTME: Backstage app-config for KubeAuto Day IDP
# ABOUTME: Uses static catalog locations, ArgoCD plugin, and Kubernetes plugin

app:
  title: KubeAuto Day IDP
  baseUrl: http://localhost:3000

organization:
  name: KubeAuto Day

backend:
  baseUrl: http://localhost:7007
  listen:
    port: 7007
  database:
    client: better-sqlite3
    connection: ':memory:'

# --- Catalog: Static File Locations ---
# No GitHub token needed. Files are loaded from local paths or URLs.
catalog:
  rules:
    - allow: [Component, System, API, Resource, Location, Template]
  locations:
    # Root catalog file
    - type: file
      target: /app/catalog/catalog-info.yaml
    # Software templates
    - type: file
      target: /app/templates/deploy-service/template.yaml
    - type: file
      target: /app/templates/create-namespace/template.yaml
    # Sample app
    - type: file
      target: /app/catalog/systems/sample-app.yaml

# --- ArgoCD Plugin ---
argocd:
  # The base URL of the ArgoCD API server
  baseUrl: https://argocd-server.argocd.svc.cluster.local
  # Authentication: use an ArgoCD API token stored in a K8s secret (via ESO)
  # The token is injected as an environment variable
  token: ${ARGOCD_AUTH_TOKEN}

# --- Kubernetes Plugin ---
kubernetes:
  serviceLocatorMethod:
    type: multiTenant
  clusterLocatorMethods:
    - type: config
      clusters:
        - name: kubeauto-eks
          url: https://kubernetes.default.svc
          authProvider: serviceAccount
          serviceAccountToken: ${K8S_SA_TOKEN}
          skipTLSVerify: true
          skipMetricsLookup: true

# --- Auth (Phase 7 — OIDC) ---
# Uncomment in Phase 7 when GitHub OAuth App is configured
# auth:
#   environment: production
#   providers:
#     github:
#       production:
#         clientId: ${GITHUB_CLIENT_ID}
#         clientSecret: ${GITHUB_CLIENT_SECRET}

# --- TechDocs ---
techdocs:
  builder: local
  generator:
    runIn: local
  publisher:
    type: local
```

### catalog-info.yaml Annotations for Plugins

Each component registered in the catalog needs specific annotations for plugins to discover it.

```yaml
# ABOUTME: Catalog entry for the sample Flask app
# ABOUTME: Annotations wire ArgoCD and Kubernetes plugins to this component
apiVersion: backstage.io/v1alpha1
kind: Component
metadata:
  name: sample-app
  description: Sample Python Flask application with OTel instrumentation
  annotations:
    # ArgoCD plugin — must match the ArgoCD Application name exactly
    argocd/app-name: sample-app

    # Kubernetes plugin — label selector to find pods
    backstage.io/kubernetes-label-selector: "app=sample-app"
    # Kubernetes plugin — namespace(s) to search
    backstage.io/kubernetes-namespace: apps

    # TechDocs — path to mkdocs.yml relative to catalog-info.yaml
    backstage.io/techdocs-ref: dir:.
  tags:
    - python
    - flask
    - otel
spec:
  type: service
  lifecycle: production
  owner: platform-team
  system: kubeauto-idp
```

### Software Template Format (backstage/templates/deploy-service/template.yaml)

```yaml
# ABOUTME: Backstage software template for deploying a new service
# ABOUTME: Creates K8s manifests and ArgoCD Application compliant with Kyverno policies
apiVersion: scaffolder.backstage.io/v1beta3
kind: Template
metadata:
  name: deploy-service
  title: Deploy a New Service
  description: Creates a Kubernetes deployment with ArgoCD Application, compliant with all Kyverno policies
  tags:
    - kubernetes
    - argocd
    - recommended
spec:
  owner: platform-team
  type: service

  parameters:
    - title: Service Details
      required:
        - name
        - owner
        - image
      properties:
        name:
          title: Service Name
          type: string
          description: Unique name for the service (lowercase, alphanumeric, hyphens)
          pattern: '^[a-z0-9][a-z0-9-]*[a-z0-9]$'
        owner:
          title: Owner Team
          type: string
          description: Team that owns this service
          default: platform-team
        image:
          title: Container Image
          type: string
          description: "Full image reference (e.g., docker.io/library/nginx:latest)"
        replicas:
          title: Replicas
          type: integer
          default: 2
          minimum: 1
          maximum: 5
        port:
          title: Container Port
          type: integer
          default: 8080

  steps:
    - id: fetch-skeleton
      name: Fetch Skeleton
      action: fetch:template
      input:
        url: ./skeleton
        values:
          name: ${{ parameters.name }}
          owner: ${{ parameters.owner }}
          image: ${{ parameters.image }}
          replicas: ${{ parameters.replicas }}
          port: ${{ parameters.port }}

    - id: publish
      name: Write to GitOps Repo
      action: publish:file
      input:
        path: gitops/apps/${{ parameters.name }}

  output:
    links:
      - title: ArgoCD Application
        url: https://argocd.example.com/applications/${{ parameters.name }}
```

### Skeleton Template File (backstage/templates/deploy-service/skeleton/deployment.yaml)

All generated resources MUST comply with Kyverno policies in the `apps` namespace:

```yaml
# ABOUTME: Skeleton deployment template for Backstage scaffolder
# ABOUTME: Pre-compliant with all Kyverno policies (labels, limits, probes, non-privileged)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${{ values.name }}
  namespace: apps
  labels:
    app: ${{ values.name }}
    team: ${{ values.owner }}
spec:
  replicas: ${{ values.replicas }}
  selector:
    matchLabels:
      app: ${{ values.name }}
  template:
    metadata:
      labels:
        app: ${{ values.name }}
        team: ${{ values.owner }}
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
        - name: ${{ values.name }}
          image: ${{ values.image }}
          ports:
            - containerPort: ${{ values.port }}
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 256Mi
          readinessProbe:
            httpGet:
              path: /healthz
              port: ${{ values.port }}
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /healthz
              port: ${{ values.port }}
            initialDelaySeconds: 10
            periodSeconds: 30
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop:
                - ALL
```

---

## Guardrail Integration

Backstage implements **Guardrail #1** at Layer 3 (Kubernetes Infrastructure).

| Guardrail | How Backstage Implements It |
|-----------|----------------------------|
| **#1 Propose-Approve-Execute** | Software templates enforce a structured propose-approve-execute workflow for developers. Templates produce Kyverno-compliant resources (labels, limits, probes, non-privileged). Developers propose via template, platform team approves via catalog review, ArgoCD executes via GitOps sync. |

**Backstage + Kyverno synergy:** Templates generate compliant resources at creation time (shift-left). Kyverno validates at admission time (defense-in-depth). If a template produces non-compliant resources, Kyverno rejects them — this catches template bugs before they reach production.

**Layer 2 enforcement:** No direct Layer 2 hooks for Backstage. The catalog is populated via static file locations and ConfigMap mounts.

---

### Root Catalog File (backstage/catalog/catalog-info.yaml)

```yaml
# ABOUTME: Root Backstage catalog file for the KubeAuto Day IDP
# ABOUTME: References all systems, components, and templates via static locations
apiVersion: backstage.io/v1alpha1
kind: System
metadata:
  name: kubeauto-idp
  description: KubeAuto Day Internal Developer Platform
spec:
  owner: platform-team
```

---

## Common Mistakes

### Mistake 1: Using the legacy backend system
```typescript
// WRONG — this was removed in early 2025
import { createServiceBuilder } from '@backstage/backend-common';
const service = createServiceBuilder(module)
  .loadConfig(configReader)
  .addRouter('/catalog', await catalog(catalogEnv))
```
Fix: Use `createBackend()` from `@backstage/backend-defaults`. See the correct pattern above.

### Mistake 2: Using GitHub discovery for catalog without a token
```yaml
# WRONG for initial setup — requires a GitHub token
catalog:
  providers:
    github:
      organization: my-org
```
Fix: Use `type: file` or `type: url` locations initially. Add GitHub discovery in Phase 7 or later when tokens are configured.

### Mistake 3: Wrong annotation key for ArgoCD plugin
```yaml
# WRONG — this was the old annotation format
annotations:
  argocd/app-selector: app=my-app
```
Fix: Use `argocd/app-name: <exact-application-name>` to match the ArgoCD Application resource name.

### Mistake 4: Missing Kubernetes namespace annotation
```yaml
# WRONG — Kubernetes plugin cannot find pods without namespace
annotations:
  backstage.io/kubernetes-label-selector: "app=my-app"
  # Missing: backstage.io/kubernetes-namespace: apps
```
Fix: Always include both `backstage.io/kubernetes-label-selector` AND `backstage.io/kubernetes-namespace`.

### Mistake 5: Template skeleton files not compliant with Kyverno
If the skeleton generates resources without labels, resource limits, probes, or with privileged containers, Kyverno will reject them in the `apps` namespace. Every skeleton MUST include:
- `app` and `team` labels on pods
- CPU and memory `requests` and `limits`
- `readinessProbe` and `livenessProbe`
- `securityContext.runAsNonRoot: true`
- `securityContext.allowPrivilegeEscalation: false`

### Mistake 6: Using deprecated scaffolder API version
```yaml
# WRONG — v1beta2 is deprecated
apiVersion: scaffolder.backstage.io/v1beta2
```
Fix: Use `scaffolder.backstage.io/v1beta3` for template definitions.

### Mistake 7: Referencing old plugin package names
```typescript
// WRONG — old package naming
import '@backstage/plugin-catalog-backend';
```
Fix: For the new backend system, many plugins use the `/alpha` export path:
```typescript
backend.add(import('@backstage/plugin-catalog-backend/alpha'));
```
Check each plugin's current documentation for the correct import path.

### Mistake 8: Hardcoding secrets in app-config.yaml
```yaml
# WRONG — secrets must come from environment variables via ESO
argocd:
  token: "argocd-admin-token-abc123"
```
Fix: Use `${ENV_VAR}` substitution. Inject secrets as environment variables from K8s secrets managed by External Secrets Operator.

### Mistake 9: Database config for production
```yaml
# WRONG for production — SQLite is for dev only
backend:
  database:
    client: better-sqlite3
    connection: ':memory:'
```
For a demo/conference environment, SQLite is acceptable. For production, use PostgreSQL. Since this is a demo IDP, SQLite is fine but note the limitation.

---

## Validation Commands

```bash
# Verify Backstage pod is running
kubectl get pods -n backstage -l app.kubernetes.io/name=backstage

# Check Backstage logs for startup errors (plugin wiring issues show here)
kubectl logs -n backstage -l app.kubernetes.io/name=backstage --tail=50

# Test Backstage UI accessibility
kubectl port-forward -n backstage svc/backstage 7007:7007 &
curl -s -o /dev/null -w "%{http_code}" http://localhost:7007
# Should return 200

# Verify catalog has entities
curl -s http://localhost:7007/api/catalog/entities | python3 -m json.tool | head -20
# Should show at least one entity

# Verify templates are registered
curl -s "http://localhost:7007/api/catalog/entities?filter=kind=template" | python3 -m json.tool
# Should show deploy-service and create-namespace templates

# Verify ArgoCD plugin connectivity
curl -s http://localhost:7007/api/argocd/applications | python3 -m json.tool
# Should return ArgoCD applications list (or auth error if token not set)

# Verify Kubernetes plugin connectivity
curl -s http://localhost:7007/api/kubernetes/clusters | python3 -m json.tool
# Should return cluster info

# Check that static catalog locations loaded
kubectl logs -n backstage -l app.kubernetes.io/name=backstage --tail=100 | grep -i "location"
# Should see locations being processed without errors

# Verify no deprecated backend warnings in logs
kubectl logs -n backstage -l app.kubernetes.io/name=backstage --tail=100 | grep -i "deprecated"
# Should be clean — any deprecation warnings indicate old patterns
```
