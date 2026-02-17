# Kyverno Policies Skill — KubeAuto Day IDP

This skill encodes correct patterns for Kyverno 1.17+ policy authoring.
The critical constraint: enforce mode ONLY in the `apps` namespace.
All system namespaces must be excluded to prevent policies from blocking
platform components (ArgoCD, Prometheus, Kyverno itself, etc.).

---

## Correct Patterns

### Namespace Exclusion Strategy

Every ClusterPolicy MUST exclude system namespaces. Kyverno 1.17+ supports
namespace selectors and explicit exclusions. Use BOTH for defense-in-depth.

The full exclusion list for this project:

```yaml
# These namespaces MUST be excluded from ALL enforce policies:
# - kube-system
# - kube-public
# - kube-node-lease
# - kyverno
# - argocd
# - monitoring
# - backstage
# - platform
# - security
# - cert-manager
# - ingress-nginx (or aws-load-balancer-controller namespace)
```

### ClusterPolicy Template (Traditional, Not CEL)

Kyverno 1.17 promoted CEL policies to v1 stable, but this project uses
traditional ClusterPolicy for broader community familiarity. CEL policies
are acceptable but not required.

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-labels
  annotations:
    policies.kyverno.io/title: Require Labels
    policies.kyverno.io/category: Best Practices
    policies.kyverno.io/severity: medium
    policies.kyverno.io/description: >-
      Require all pods in the apps namespace to have app and version labels.
spec:
  validationFailureAction: Enforce    # Enforce ONLY because match targets apps NS
  background: true
  rules:
    - name: require-app-label
      match:
        any:
          - resources:
              kinds:
                - Pod
              namespaces:
                - apps                 # ONLY target the apps namespace
      validate:
        message: "The label 'app' is required."
        pattern:
          metadata:
            labels:
              app: "?*"
    - name: require-version-label
      match:
        any:
          - resources:
              kinds:
                - Pod
              namespaces:
                - apps
      validate:
        message: "The label 'version' is required."
        pattern:
          metadata:
            labels:
              version: "?*"
```

### Policy: Restrict Image Registries

Only allow images from trusted registries in the `apps` namespace.

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: restrict-image-registries
  annotations:
    policies.kyverno.io/title: Restrict Image Registries
    policies.kyverno.io/category: Security
    policies.kyverno.io/severity: high
spec:
  validationFailureAction: Enforce
  background: true
  rules:
    - name: validate-registries
      match:
        any:
          - resources:
              kinds:
                - Pod
              namespaces:
                - apps
      validate:
        message: >-
          Images must come from allowed registries:
          ghcr.io, docker.io/library, or the project ECR.
        pattern:
          spec:
            containers:
              - image: "ghcr.io/* | docker.io/library/* | *.dkr.ecr.*.amazonaws.com/*"
            =(initContainers):
              - image: "ghcr.io/* | docker.io/library/* | *.dkr.ecr.*.amazonaws.com/*"
```

### Policy: Require Resource Limits

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-resource-limits
  annotations:
    policies.kyverno.io/title: Require Resource Limits
    policies.kyverno.io/category: Best Practices
    policies.kyverno.io/severity: medium
spec:
  validationFailureAction: Enforce
  background: true
  rules:
    - name: require-limits
      match:
        any:
          - resources:
              kinds:
                - Pod
              namespaces:
                - apps
      validate:
        message: "CPU and memory limits are required for all containers."
        pattern:
          spec:
            containers:
              - resources:
                  limits:
                    memory: "?*"
                    cpu: "?*"
```

### Policy: Disallow Privileged Containers

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: disallow-privileged
  annotations:
    policies.kyverno.io/title: Disallow Privileged Containers
    policies.kyverno.io/category: Pod Security
    policies.kyverno.io/severity: high
spec:
  validationFailureAction: Enforce
  background: true
  rules:
    - name: disallow-privileged-containers
      match:
        any:
          - resources:
              kinds:
                - Pod
              namespaces:
                - apps
      validate:
        message: "Privileged containers are not allowed in the apps namespace."
        pattern:
          spec:
            containers:
              - =(securityContext):
                  =(privileged): false
            =(initContainers):
              - =(securityContext):
                  =(privileged): false
```

### Policy: Require Readiness and Liveness Probes

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-probes
  annotations:
    policies.kyverno.io/title: Require Probes
    policies.kyverno.io/category: Best Practices
    policies.kyverno.io/severity: medium
spec:
  validationFailureAction: Enforce
  background: true
  rules:
    - name: require-readiness-probe
      match:
        any:
          - resources:
              kinds:
                - Pod
              namespaces:
                - apps
      validate:
        message: "A readinessProbe is required for all containers."
        pattern:
          spec:
            containers:
              - readinessProbe: {}
    - name: require-liveness-probe
      match:
        any:
          - resources:
              kinds:
                - Pod
              namespaces:
                - apps
      validate:
        message: "A livenessProbe is required for all containers."
        pattern:
          spec:
            containers:
              - livenessProbe: {}
```

### Policy: Require NetworkPolicy Exists (Audit Only)

This policy audits whether a NetworkPolicy exists for each app. Use audit
mode because it validates cluster state, not individual pod spec.

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-networkpolicy
  annotations:
    policies.kyverno.io/title: Require NetworkPolicy
    policies.kyverno.io/category: Networking
    policies.kyverno.io/severity: medium
spec:
  validationFailureAction: Audit    # Audit, not Enforce — informational
  background: true
  rules:
    - name: require-netpol
      match:
        any:
          - resources:
              kinds:
                - Deployment
              namespaces:
                - apps
      preconditions:
        all:
          - key: "{{request.operation}}"
            operator: In
            value: ["CREATE", "UPDATE"]
      validate:
        message: "A NetworkPolicy should exist for this application."
        deny:
          conditions:
            all:
              - key: "{{request.object.metadata.labels.app}}"
                operator: Equals
                value: ""
```

### PSS Labels as Defense-in-Depth Companion

Kyverno enforce policies and PSS namespace labels serve complementary roles:
- PSS labels are enforced by the Kubernetes API server admission controller
- Kyverno policies provide more granular rules (labels, registries, probes)

Both should be active on the `apps` namespace.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: apps
  labels:
    # PSS labels — enforced by K8s API server
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
    # Kyverno policies also enforce in this namespace (see policies above)
```

### Resource Quotas on `apps` Namespace

Complement Kyverno resource-limits policy with namespace-level quotas.

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: apps-quota
  namespace: apps
spec:
  hard:
    pods: "10"
    requests.cpu: "4"
    requests.memory: "8Gi"
    limits.cpu: "4"
    limits.memory: "8Gi"
```

### Kyverno Helm Installation Values

```yaml
# Kyverno 1.17+ Helm values
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: kyverno
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: "-5"
spec:
  project: platform
  source:
    chart: kyverno
    repoURL: https://kyverno.github.io/kyverno
    targetRevision: "3.3.*"    # Chart 3.x = Kyverno 1.17+
    helm:
      valuesObject:
        # Exclude Kyverno's own namespace from webhooks to prevent deadlock
        config:
          webhooks:
            - namespaceSelector:
                matchExpressions:
                  - key: kubernetes.io/metadata.name
                    operator: NotIn
                    values:
                      - kyverno
                      - kube-system
                      - kube-public
                      - kube-node-lease
        # Resource limits for Kyverno itself
        resources:
          limits:
            memory: 512Mi
            cpu: 500m
          requests:
            memory: 256Mi
            cpu: 100m
  destination:
    server: https://kubernetes.default.svc
    namespace: kyverno
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

---

## Common Mistakes

### CRITICAL: Do NOT enforce policies across all namespaces

```yaml
# WRONG — this will break ArgoCD, Prometheus, Kyverno itself, etc.
spec:
  validationFailureAction: Enforce
  rules:
    - name: my-rule
      match:
        any:
          - resources:
              kinds:
                - Pod
              # No namespace filter = ALL namespaces = disaster
```

Always explicitly scope enforce policies to the `apps` namespace only.

### CRITICAL: Do NOT forget to exclude system namespaces from webhooks

If Kyverno's webhook intercepts its own namespace, a deadlock can occur
where Kyverno cannot start because its own policies reject its pods.

```yaml
# WRONG — no namespace exclusion on webhooks
config:
  webhooks: []

# CORRECT — exclude kyverno and kube-system at minimum
config:
  webhooks:
    - namespaceSelector:
        matchExpressions:
          - key: kubernetes.io/metadata.name
            operator: NotIn
            values:
              - kyverno
              - kube-system
```

### Do NOT use `exclude` blocks when `match.namespaces` is sufficient

```yaml
# OVERLY COMPLEX — listing every system namespace in exclude
spec:
  rules:
    - name: my-rule
      match:
        any:
          - resources:
              kinds:
                - Pod
      exclude:
        any:
          - resources:
              namespaces:
                - kube-system
                - kyverno
                - argocd
                - monitoring
                # ... many more

# SIMPLER AND SAFER — only match the target namespace
spec:
  rules:
    - name: my-rule
      match:
        any:
          - resources:
              kinds:
                - Pod
              namespaces:
                - apps        # Only this namespace is targeted
```

Using `match.namespaces: [apps]` is an allowlist approach (safer).
Using `exclude` is a denylist approach (fragile — new namespaces are exposed by default).

### Do NOT use CEL policies unless explicitly chosen

```yaml
# NOT WRONG but not the project convention — traditional ClusterPolicy is preferred
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: my-policy
spec:
  rules:
    - name: my-rule
      match:
        any:
          - resources:
              kinds:
                - Pod
      validate:
        cel:
          expressions:
            - expression: "object.spec.containers.all(c, has(c.resources.limits))"
```

CEL policies are stable in 1.17+ but this project uses traditional validate/pattern
syntax for broader audience familiarity at the conference.

### Do NOT apply enforce policies to Deployments instead of Pods

Kyverno evaluates Pods at admission time. If you match Deployments, the policy
checks the Deployment spec but the actual Pod might differ (injected sidecars, etc.).

```yaml
# LESS EFFECTIVE — matches Deployment, not the actual Pod
match:
  any:
    - resources:
        kinds:
          - Deployment

# CORRECT — matches Pod (what actually runs)
match:
  any:
    - resources:
        kinds:
          - Pod
```

### Do NOT set validationFailureAction globally when it should differ per rule

If some rules should enforce and others should audit, use per-rule
`validationFailureAction` overrides (supported in Kyverno 1.17+).

```yaml
spec:
  # Default for the policy
  validationFailureAction: Enforce
  rules:
    - name: strict-rule
      # Inherits Enforce from policy level
      validate:
        # ...
    - name: informational-rule
      validate:
        validationFailureAction: Audit  # Override to Audit for this rule only
        # ...
```

---

## Validation Commands

```bash
# Verify Kyverno is running and healthy
kubectl -n kyverno get pods

# Verify Kyverno version is 1.17+
kubectl -n kyverno get deploy kyverno-admission-controller \
  -o jsonpath='{.spec.template.spec.containers[0].image}'

# List all ClusterPolicies
kubectl get clusterpolicies

# Verify all policies are in Ready state
kubectl get clusterpolicies -o jsonpath='{range .items[*]}{.metadata.name}: {.status.conditions[?(@.type=="Ready")].status}{"\n"}{end}'

# Verify enforce policies only target the apps namespace
kubectl get clusterpolicies -o yaml | grep -A5 "namespaces:" | head -30

# Test a policy by creating a non-compliant pod in apps namespace (should be blocked)
kubectl run test-no-labels --image=nginx -n apps --dry-run=server
# Expected: denied by require-labels policy

# Test that the same pod is allowed in a system namespace (should succeed)
kubectl run test-no-labels --image=nginx -n default --dry-run=server
# Expected: allowed (policy does not target default namespace)

# Verify Kyverno webhook configuration excludes system namespaces
kubectl get mutatingwebhookconfigurations kyverno-resource-mutating-webhook-cfg -o yaml | \
  grep -A10 "namespaceSelector"

# Check policy violation reports
kubectl get policyreport -A
kubectl get clusterpolicyreport

# Verify PSS labels on apps namespace
kubectl get namespace apps -o jsonpath='{.metadata.labels}' | \
  python3 -m json.tool | grep pod-security

# Verify resource quota on apps namespace
kubectl -n apps describe resourcequota apps-quota

# Test resource limits enforcement
cat <<'EOF' | kubectl apply -n apps --dry-run=server -f -
apiVersion: v1
kind: Pod
metadata:
  name: test-no-limits
  labels:
    app: test
    version: v1
spec:
  containers:
    - name: test
      image: docker.io/library/nginx:latest
EOF
# Expected: denied by require-resource-limits policy

# Verify a compliant pod is accepted
cat <<'EOF' | kubectl apply -n apps --dry-run=server -f -
apiVersion: v1
kind: Pod
metadata:
  name: test-compliant
  labels:
    app: test
    version: v1
spec:
  containers:
    - name: test
      image: docker.io/library/nginx:latest
      resources:
        limits:
          cpu: 100m
          memory: 128Mi
        requests:
          cpu: 50m
          memory: 64Mi
      readinessProbe:
        httpGet:
          path: /
          port: 80
      livenessProbe:
        httpGet:
          path: /
          port: 80
      securityContext:
        privileged: false
        runAsNonRoot: true
        allowPrivilegeEscalation: false
        capabilities:
          drop:
            - ALL
        seccompProfile:
          type: RuntimeDefault
EOF
# Expected: accepted (all policies pass)

# Check Kyverno admission controller logs for errors
kubectl -n kyverno logs deploy/kyverno-admission-controller --tail=50
```
