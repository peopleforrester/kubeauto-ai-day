# Falco Rules — Skill File

## Status

Falco is **CNCF Graduated** (not Sandbox, not Incubating). Always reference it as Graduated.

## Driver: eBPF (Default)

Since Falco 0.38.0, the **eBPF driver is the default**. On EKS, there is no kernel module needed. Do NOT set `driver.kind: module` or try to install kernel headers. The correct Helm values are:

```yaml
driver:
  kind: modern_ebpf    # Default since 0.38.0; explicit for clarity
```

If you see `driver.kind: module` or `driver.kind: ebpf` (classic eBPF), that is outdated. `modern_ebpf` uses CO-RE (Compile Once, Run Everywhere) and requires no kernel headers on the node.

## Deployment Pattern

Falco runs as a **DaemonSet** — one pod per node. It must see syscalls from every node. Do NOT deploy it as a Deployment or StatefulSet.

Falcosidekick is a separate **Deployment** (typically 1-2 replicas) that receives Falco events and forwards them to backends like Prometheus.

---

## Correct Patterns

### Helm Values for EKS (gitops/apps/falco/values.yaml)

```yaml
# ABOUTME: Falco Helm values for EKS with eBPF driver
# ABOUTME: Configures runtime threat detection DaemonSet with custom rules
driver:
  kind: modern_ebpf

tty: true

falco:
  grpc:
    enabled: true
  grpc_output:
    enabled: true
  json_output: true
  log_stderr: true
  log_syslog: false
  priority: notice
  # Load custom rules from ConfigMap
  rules_file:
    - /etc/falco/falco_rules.yaml
    - /etc/falco/falco_rules.local.yaml
    - /etc/falco/rules.d

# Mount custom rules from ConfigMap
customRules:
  custom-rules.yaml: |
    # Content from security/falco/custom-rules.yaml
  eks-aware-rules.yaml: |
    # Content from security/falco/eks-aware-rules.yaml

tolerations:
  - effect: NoSchedule
    operator: Exists

resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

### ArgoCD Application (gitops/apps/falco/application.yaml)

```yaml
# ABOUTME: ArgoCD Application for Falco runtime security
# ABOUTME: Deploys Falco DaemonSet to security namespace via Helm
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: falco
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: "3"
spec:
  project: default
  source:
    repoURL: https://falcosecurity.github.io/charts
    chart: falco
    targetRevision: "4.*"     # Falco Helm chart 4.x series
    helm:
      valueFiles:
        - values.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: security
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=false
```

### Custom Rule Syntax (security/falco/custom-rules.yaml)

Falco rules have three building blocks: **macros**, **lists**, and **rules**.

```yaml
# ABOUTME: Custom Falco rules for KubeAuto Day IDP
# ABOUTME: Detects exec-into-pod, sensitive file access, unexpected outbound connections

# --- Lists ---
- list: allowed_outbound_ports
  items: [53, 443, 6443, 8080, 8443, 9090, 4317, 4318]

- list: sensitive_file_paths
  items:
    - /etc/shadow
    - /etc/kubernetes/pki
    - /var/run/secrets/kubernetes.io/serviceaccount/token
    - /root/.kube/config
    - /root/.aws/credentials

- list: trusted_images
  items:
    - docker.io/library
    - public.ecr.aws
    - registry.k8s.io
    - quay.io/argoproj
    - ghcr.io/kyverno
    - docker.io/falcosecurity
    - docker.io/grafana
    - quay.io/prometheus

# --- Macros ---
- macro: in_apps_namespace
  condition: k8s.ns.name = "apps"

- macro: is_exec_event
  condition: >
    evt.type = execve and
    container.id != host and
    proc.pname = runc:[2:INIT]

# --- Rules ---

# Rule 1: Detect exec into pod
- rule: Exec Into Pod Detected
  desc: >
    Detect when someone runs kubectl exec or equivalent to get a shell in a
    running container. This is a common attack vector post-compromise.
  condition: >
    spawned_process and
    container and
    k8s.ns.name != "" and
    proc.pname in (runc:[2:INIT], cri-o, containerd-shim) and
    proc.name in (bash, sh, dash, zsh, csh, fish, tcsh)
  output: >
    Shell spawned in container
    (user=%user.name pod=%k8s.pod.name ns=%k8s.ns.name container=%container.name
     shell=%proc.name parent=%proc.pname cmdline=%proc.cmdline
     image=%container.image.repository)
  priority: WARNING
  tags: [container, shell, mitre_execution]
  source: syscall

# Rule 2: Sensitive file access
- rule: Sensitive File Read in Container
  desc: >
    Detect when a process inside a container reads sensitive files such as
    service account tokens, shadow files, or cloud credentials.
  condition: >
    open_read and
    container and
    fd.name pmatch (sensitive_file_paths) and
    not proc.name in (kubelet, kube-proxy, coredns)
  output: >
    Sensitive file read in container
    (user=%user.name file=%fd.name pod=%k8s.pod.name ns=%k8s.ns.name
     container=%container.name image=%container.image.repository
     cmdline=%proc.cmdline)
  priority: CRITICAL
  tags: [container, filesystem, mitre_credential_access]
  source: syscall

# Rule 3: Unexpected outbound connection
- rule: Unexpected Outbound Connection from Apps
  desc: >
    Detect outbound network connections from the apps namespace to ports
    not in the allowed list. May indicate data exfiltration or C2 callback.
  condition: >
    outbound and
    container and
    in_apps_namespace and
    not fd.sport in (allowed_outbound_ports)
  output: >
    Unexpected outbound connection from apps namespace
    (pod=%k8s.pod.name ns=%k8s.ns.name container=%container.name
     image=%container.image.repository connection=%fd.name
     dest_port=%fd.sport cmdline=%proc.cmdline)
  priority: WARNING
  tags: [container, network, mitre_exfiltration]
  source: syscall
```

### EKS-Specific Rules (security/falco/eks-aware-rules.yaml)

```yaml
# ABOUTME: Falco rules specific to EKS runtime environment
# ABOUTME: Covers EKS node agent patterns and AWS metadata access

# Detect access to EC2 instance metadata service from containers
- rule: Container Accessing EC2 Metadata
  desc: >
    Detect when a container tries to reach the EC2 instance metadata service
    (169.254.169.254). On EKS with Pod Identity, containers should not need
    direct IMDS access. This may indicate credential theft attempts.
  condition: >
    outbound and
    container and
    fd.sip = "169.254.169.254"
  output: >
    Container accessing EC2 metadata service (IMDS)
    (pod=%k8s.pod.name ns=%k8s.ns.name container=%container.name
     image=%container.image.repository cmdline=%proc.cmdline)
  priority: CRITICAL
  tags: [container, network, aws, mitre_credential_access]
  source: syscall

# Detect writes to /etc inside containers (configuration tampering)
- rule: Write Below Etc in Container
  desc: >
    Detect file writes under /etc inside a container. Legitimate containers
    rarely modify /etc. This may indicate persistence or config tampering.
  condition: >
    write_etc_common and
    container and
    not proc.name in (sed, tee) and
    not k8s.ns.name in (kube-system, kyverno, argocd, monitoring, security)
  output: >
    Write below /etc in container
    (user=%user.name file=%fd.name pod=%k8s.pod.name ns=%k8s.ns.name
     container=%container.name image=%container.image.repository)
  priority: WARNING
  tags: [container, filesystem, mitre_persistence]
  source: syscall
```

---

## Guardrail Integration

Falco implements **Guardrails #3 and #5** at Layer 3 (Kubernetes Infrastructure).

| Guardrail | How Falco Implements It |
|-----------|------------------------|
| **#3 Stop Hooks & Circuit Breakers** | Runtime detection of anomalous behavior: exec into containers, sensitive file reads, unexpected outbound connections, IMDS access, /etc writes. Falco is detection-only (does not block), but alerts enable rapid human response. |
| **#5 Immutable Audit Trail** | Syscall-level event logging provides an immutable record of what happened inside containers. Falcosidekick exports to Prometheus metrics, creating a queryable audit trail in Grafana dashboards. |

**Falco is detection, not prevention.** Use Kyverno for admission-time blocking and NetworkPolicies for network blocking. Falco tells you what happened after the fact — which is essential for incident response and the audit trail.

**Layer 2 enforcement:** No direct Layer 2 hooks for Falco. The `cc-posttool-audit.sh` hook reminds operators to verify after applying changes.

---

### Falcosidekick Values (security/falcosidekick/values.yaml)

```yaml
# ABOUTME: Falcosidekick configuration for forwarding Falco alerts
# ABOUTME: Exports to Prometheus metrics endpoint for Grafana dashboards
config:
  prometheus:
    # Expose /metrics endpoint for Prometheus scraping
    extralabels: ""
  webhook:
    # Optional: forward to a custom webhook
    # address: ""

# Create a ServiceMonitor for Prometheus to scrape Falcosidekick metrics
webui:
  enabled: false

# Prometheus exporter settings
podAnnotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "2801"
  prometheus.io/path: "/metrics"

replicaCount: 2

resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 100m
    memory: 128Mi
```

---

## Common Mistakes

### Mistake 1: Using kernel module driver on EKS
```yaml
# WRONG - kernel module requires headers not available on EKS AMIs
driver:
  kind: module
```
Fix: Use `modern_ebpf`. It is the default since 0.38.0 and works on EKS without kernel headers.

### Mistake 2: Deploying Falco as a Deployment
```yaml
# WRONG - Falco must run on every node to see all syscalls
kind: Deployment
replicas: 2
```
Fix: Falco uses a DaemonSet. The Helm chart handles this automatically. Do not override `kind`.

### Mistake 3: Referencing Falco as CNCF Sandbox or Incubating
Falco is **CNCF Graduated** (graduated February 2024). Any reference to Sandbox or Incubating is wrong.

### Mistake 4: Using old eBPF driver instead of modern_ebpf
```yaml
# WRONG - classic eBPF driver (deprecated path)
driver:
  kind: ebpf
```
Fix: Use `modern_ebpf` which uses CO-RE and does not require per-kernel BPF object files.

### Mistake 5: Missing syscall source field in rules
```yaml
# WRONG - missing source field
- rule: My Rule
  condition: spawned_process and container
  output: something happened
  priority: WARNING
```
Fix: Always include `source: syscall` for system call based rules. Without it, the rule may not fire.

### Mistake 6: Putting Falcosidekick in the same Helm release as Falco
Falcosidekick is a **separate chart** (`falcosecurity/falcosidekick`), not a sub-chart of Falco. Deploy it as its own ArgoCD Application in the security namespace.

### Mistake 7: Not excluding system namespaces in custom rules
Rules that trigger in kube-system, kyverno, argocd, monitoring namespaces will be extremely noisy and generate false positives. Always scope rules with namespace conditions or exclude system namespaces explicitly.

### Mistake 8: Expecting Falco to block actions
Falco is **detection only** — it does not block or prevent actions. It observes syscalls and generates alerts. Use Kyverno for admission-time blocking and NetworkPolicies for network blocking. Falco tells you what happened after the fact.

---

## Validation Commands

```bash
# Verify Falco DaemonSet is running on all nodes
kubectl get ds -n security falco -o wide
# Pod count should match node count

# Verify Falco pods are ready
kubectl get pods -n security -l app.kubernetes.io/name=falco

# Check Falco logs for successful eBPF probe loading
kubectl logs -n security -l app.kubernetes.io/name=falco --tail=20 | grep -i "ebpf"
# Should see: "modern_ebpf engine loaded successfully" or similar

# Check that custom rules loaded
kubectl logs -n security -l app.kubernetes.io/name=falco --tail=50 | grep -i "rule"
# Should see custom rule names being loaded

# Trigger a test alert: exec into any pod
kubectl exec -it -n apps <pod-name> -- /bin/sh -c "echo test"
# Then check Falco logs for the alert:
kubectl logs -n security -l app.kubernetes.io/name=falco --tail=10

# Verify Falcosidekick is running
kubectl get pods -n security -l app.kubernetes.io/name=falcosidekick

# Check Falcosidekick metrics endpoint
kubectl port-forward -n security svc/falcosidekick 2801:2801 &
curl -s http://localhost:2801/metrics | grep falco
# Should see falcosidekick_inputs_total and similar metrics

# Verify Falcosidekick receives events from Falco
kubectl logs -n security -l app.kubernetes.io/name=falcosidekick --tail=20

# Check Falco gRPC output is enabled (required for Falcosidekick)
kubectl get cm -n security falco -o yaml | grep -A5 grpc
```
