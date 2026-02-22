# ArgoCD Patterns Skill — KubeAuto Day IDP

This skill encodes correct patterns for ArgoCD 3.2+. The entire ArgoCD 2.x line
is END OF LIFE. Most tutorials, blog posts, and Stack Overflow answers reference
2.x patterns that will produce broken or deprecated configurations.

**When in doubt, assume a pattern you recall is from 2.x and verify it here.**

---

## Correct Patterns

### Helm Chart Installation (3.x)

ArgoCD 3.x uses the `argo-cd` Helm chart from the official OCI registry.

```yaml
# ArgoCD 3.2+ Helm values
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: argocd
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: "-5"
spec:
  project: default
  source:
    chart: argo-cd
    repoURL: https://argoproj.github.io/argo-helm
    targetRevision: "7.8.*"    # 7.x chart = ArgoCD 3.x
    helm:
      valuesObject:
        # 3.x: annotation-based tracking is the DEFAULT
        # Do NOT set tracking method to "label" — that is legacy 2.x behavior
        server:
          extraArgs:
            - --insecure  # If terminated at LB/ingress
        configs:
          params:
            # 30-second reconciliation for demo purposes (default is 3 minutes)
            timeout.reconciliation: "30s"
          cm:
            # Self-heal: auto-correct drift
            application.resourceTrackingMethod: "annotation"  # This is default in 3.x, explicit for clarity
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

### Annotation-Based Tracking (Default in 3.x)

ArgoCD 3.x defaults to annotation-based resource tracking. It uses the
`argocd.argoproj.io/tracking-id` annotation on managed resources.

```yaml
# You do NOT need to set this — it is the default in 3.x
# Shown for awareness only
configs:
  cm:
    application.resourceTrackingMethod: "annotation"
```

Do NOT set `application.resourceTrackingMethod: "label"` — that is the legacy
2.x default and causes issues with resources that have label length limits.

### RBAC Configuration (3.x Subject Format)

ArgoCD 3.x changed the RBAC subject format for Dex/OIDC users and groups.
The prefix format now uses the SSO provider name.

```yaml
configs:
  rbac:
    policy.csv: |
      # 3.x format: role:<role-name> for built-in roles
      # 3.x format: <sso-provider>:<group-or-user> for SSO subjects

      # Grant admin to a specific OIDC group
      g, oidc:platform-admins, role:admin

      # Grant read-only to all authenticated users
      p, role:readonly, applications, get, */*, allow
      p, role:readonly, applications, list, */*, allow
      g, oidc:authenticated, role:readonly

    # Default policy for authenticated users with no matching rule
    policy.default: role:readonly

    # Scopes to request from OIDC provider
    scopes: "[groups, email]"
```

**2.x used different subject prefixes.** If you see examples with bare group
names or `sso:` prefix, those are 2.x patterns.

### App-of-Apps Pattern

The root application bootstraps all other applications via sync waves.

```yaml
# Root app-of-apps application
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: root-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/peopleforrester/kubeauto-ai-day.git
    targetRevision: main
    path: gitops/apps
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### Sync Waves

Sync waves control deployment ordering. Lower numbers deploy first.

```yaml
# gitops/apps/namespaces.yaml — wave -10 (first)
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: namespaces
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: "-10"
spec:
  project: default
  source:
    repoURL: https://github.com/peopleforrester/kubeauto-ai-day.git
    targetRevision: main
    path: gitops/base/namespaces
  destination:
    server: https://kubernetes.default.svc
  syncPolicy:
    automated:
      prune: true
      selfHeal: true

---
# gitops/apps/kyverno.yaml — wave -5 (before apps that need policies)
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: kyverno
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: "-5"
# ...

---
# gitops/apps/sample-app.yaml — wave 5 (after platform components)
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: sample-app
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: "5"
# ...
```

**Recommended wave ordering for this project:**
- Wave -10: Namespaces, CRDs
- Wave -5: Security stack (Kyverno, Falco, ESO), ArgoCD self-manage
- Wave 0: Observability (Prometheus, Grafana, OTel)
- Wave 3: Platform services (Backstage)
- Wave 5: Application workloads (sample Flask app)

### 30-Second Demo Sync Interval

For the demo, set a 30-second reconciliation interval so changes appear fast.

```yaml
configs:
  params:
    timeout.reconciliation: "30s"
```

**Do NOT use this in production.** The default 3-minute interval is appropriate
for real clusters. This is a demo optimization only.

### Self-Heal Policy

Self-heal automatically reverts manual changes (drift) to match Git state.

```yaml
syncPolicy:
  automated:
    prune: true      # Remove resources deleted from Git
    selfHeal: true   # Revert manual changes to match Git
  retry:
    limit: 5
    backoff:
      duration: 5s
      factor: 2
      maxDuration: 3m
```

### ApplicationSet for Multi-Environment (Optional)

If generating apps from a directory structure:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: platform-components
  namespace: argocd
spec:
  generators:
    - git:
        repoURL: https://github.com/peopleforrester/kubeauto-ai-day.git
        revision: main
        directories:
          - path: gitops/components/*
  template:
    metadata:
      name: "{{path.basename}}"
      namespace: argocd
    spec:
      project: default
      source:
        repoURL: https://github.com/peopleforrester/kubeauto-ai-day.git
        targetRevision: main
        path: "{{path}}"
      destination:
        server: https://kubernetes.default.svc
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
```

---

## Guardrail Integration

ArgoCD implements **Guardrails #1 and #6** at Layer 3 (Kubernetes Infrastructure).

| Guardrail | How ArgoCD Implements It |
|-----------|------------------------|
| **#1 Propose-Approve-Execute** | All changes go through Git (propose) → ArgoCD sync (approve/execute). No `kubectl apply` in production namespaces after Phase 2. Manual sync disabled for app namespaces; automated sync with self-heal for platform namespaces. |
| **#6 Automated Rollback** | Self-heal auto-reverts manual drift to match Git state. `argocd app rollback` provides instant rollback to previous revisions. Git revert is the cheapest rollback — tagged commits at each phase completion provide clean rollback points. |

**Layer 2 enforcement:** The `cc-pretool-guard.sh` hook blocks `kubectl apply/create/replace` in production namespaces after Phase 2, forcing the GitOps path.

**Layer 1 enforcement:** Pre-push test gate ensures tests pass before code reaches the repo that ArgoCD syncs from.

---

### ArgoCD Project Scoping

Restrict what the `default` project can deploy to, and create a platform project.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: platform
  namespace: argocd
spec:
  description: Platform infrastructure components
  sourceRepos:
    - "https://github.com/peopleforrester/kubeauto-ai-day.git"
    - "https://argoproj.github.io/argo-helm"
    - "https://charts.jetstack.io"
    - "https://kyverno.github.io/kyverno"
    - "https://prometheus-community.github.io/helm-charts"
    - "https://backstage.github.io/charts"
    - "https://falcosecurity.github.io/charts"
  destinations:
    - namespace: "*"
      server: https://kubernetes.default.svc
  clusterResourceWhitelist:
    - group: "*"
      kind: "*"
```

---

## Common Mistakes

### CRITICAL: Do NOT use ArgoCD 2.x Helm chart versions

```yaml
# WRONG — chart version 5.x and 6.x map to ArgoCD 2.x (EOL)
targetRevision: "5.51.6"
targetRevision: "6.7.3"

# CORRECT — chart version 7.x maps to ArgoCD 3.x
targetRevision: "7.8.*"
```

### CRITICAL: Do NOT use label-based tracking

```yaml
# WRONG — label-based tracking is legacy 2.x default
configs:
  cm:
    application.resourceTrackingMethod: "label"

# CORRECT — annotation-based tracking is the 3.x default
# Simply do not set it, or explicitly:
configs:
  cm:
    application.resourceTrackingMethod: "annotation"
```

### CRITICAL: Do NOT use 2.x RBAC subject format

```yaml
# WRONG — 2.x subject format
g, my-github-org:my-team, role:admin

# CORRECT — 3.x subject format with SSO provider prefix
g, oidc:my-github-org:my-team, role:admin
```

### Do NOT use deprecated `argocd-cm` ConfigMap keys directly

In 3.x, most configuration has moved to Helm values under `configs.params` and
`configs.cm`. Do not create raw ConfigMaps.

```yaml
# WRONG — raw ConfigMap manipulation
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-cm
data:
  timeout.reconciliation: "30s"

# CORRECT — set via Helm values
configs:
  params:
    timeout.reconciliation: "30s"
```

### Do NOT put Application resources outside the argocd namespace

```yaml
# WRONG
metadata:
  name: my-app
  namespace: default  # Applications must live in the argocd namespace

# CORRECT
metadata:
  name: my-app
  namespace: argocd
```

### Do NOT forget finalizers for pruning

Without the finalizer, deleting an Application does not clean up deployed resources.

```yaml
metadata:
  name: my-app
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
```

### Do NOT set sync interval below 30s in production

```yaml
# WRONG for production (causes excessive API calls)
timeout.reconciliation: "5s"

# ACCEPTABLE for demo only
timeout.reconciliation: "30s"

# CORRECT for production
timeout.reconciliation: "180s"  # default
```

---

## Validation Commands

```bash
# Verify ArgoCD version is 3.x
kubectl -n argocd exec deploy/argocd-server -- argocd version --short

# Verify tracking method is annotation (default in 3.x)
kubectl -n argocd get configmap argocd-cm -o jsonpath='{.data.application\.resourceTrackingMethod}'
# Should return "annotation" or be empty (annotation is default)

# Verify reconciliation timeout is 30s for demo
kubectl -n argocd get configmap argocd-cmd-params-cm -o jsonpath='{.data.timeout\.reconciliation}'

# Verify self-heal is enabled on all apps
kubectl -n argocd get applications -o jsonpath='{range .items[*]}{.metadata.name}: selfHeal={.spec.syncPolicy.automated.selfHeal}{"\n"}{end}'

# Verify all applications are synced and healthy
kubectl -n argocd get applications
# Or use argocd CLI:
argocd app list

# Check sync status of a specific app
argocd app get root-app --refresh

# Verify sync waves are ordered correctly
kubectl -n argocd get applications -o jsonpath='{range .items[*]}{.metadata.annotations.argocd\.argoproj\.io/sync-wave} {.metadata.name}{"\n"}{end}' | sort -n

# Verify RBAC policy is loaded
kubectl -n argocd get configmap argocd-rbac-cm -o yaml

# Check for any degraded or out-of-sync applications
argocd app list --status Degraded
argocd app list --status OutOfSync

# Verify app-of-apps root is managing child apps
argocd app get root-app --show-resources

# Verify chart version deployed (should be 7.x for ArgoCD 3.x)
helm -n argocd list -o json | jq '.[].chart'

# Check ArgoCD server logs for errors
kubectl -n argocd logs deploy/argocd-server --tail=50

# Verify no label-based tracking annotations on resources
kubectl get all -A -o jsonpath='{range .items[*]}{.metadata.labels.argocd\.argoproj\.io/instance}{end}'
# Should be empty; annotation-based tracking uses annotations, not labels
```
