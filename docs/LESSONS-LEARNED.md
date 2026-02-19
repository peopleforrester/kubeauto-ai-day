# Lessons Learned — AI-Assisted IDP Build

Every correction cycle, unexpected behavior, and hard-won insight from the
build. Organized by component. If you're recreating this platform, read
this first.

---

## Phase 1: Foundation

### EKS Cluster (3 correction cycles)

**Problem 1: Terraform EKS module v21 variable renames.**
The AI generated Terraform using v20 variable names (`cluster_name`,
`cluster_version`). Module v21.15 renamed them to `name` and
`kubernetes_version`. Terraform plan failed with "unsupported argument."

*Fix:* Updated variable names to match v21 API. Always check the module
changelog when pinning a major version.

**Problem 2: AWS provider 6.x dependency.**
The AI initially used AWS provider ~> 5.0 patterns. Provider 6.x changed
some resource attributes and data source behaviors.

*Fix:* Pinned `hashicorp/aws ~> 6.0` in `required_providers`. Verified
all data sources still worked.

**Problem 3: Managed addon bootstrap chicken-and-egg.**
EKS managed addons (VPC CNI, CoreDNS) can't install until the cluster
exists, but the cluster needs the VPC CNI to schedule pods. Terraform
handles this via implicit dependencies, but the first `terraform apply`
can appear to hang during addon installation.

*Fix:* No code fix needed — just patience. Addons install after cluster
is Ready. Takes 15-20 minutes total.

### IAM Roles + Pod Identity (1 correction cycle)

**Problem: IRSA vs Pod Identity confusion.**
The plan called for Pod Identity as primary, but EBS CSI Driver and AWS
LB Controller both work better with IRSA (they predate Pod Identity
support in their service account annotations).

*Fix:* Used IRSA for both EBS CSI and LB Controller. Pod Identity Agent
is installed as a managed addon for future use.

---

## Phase 2: GitOps Bootstrap

### ArgoCD Install (1 correction cycle)

**Problem: Helm chart version mapping.**
The skill file referenced chart version `7.8.*`, but the actual chart
available was from the `9.x` series for ArgoCD 3.2.6. The `7.x` chart
mapped to an older ArgoCD 3.0 release.

*Fix:* Updated to chart version `9.x` (specifically whatever was current
at install time). ArgoCD Helm chart versions do NOT follow ArgoCD
application versions — always verify the mapping.

*Key insight:* ArgoCD was bootstrapped via `helm install` from the CLI
(not Terraform), then the app-of-apps pattern took over management. The
bootstrap Helm values are in `gitops/argocd/values.yaml`.

### App-of-Apps Pattern (1 correction cycle)

**Problem: Private GitHub repo access.**
ArgoCD couldn't sync the app-of-apps root because the GitHub repo is
private. No error in the Application status — just stuck "Progressing."

*Fix:* Created a Kubernetes Secret with GitHub PAT in the argocd namespace,
labeled with `argocd.argoproj.io/secret-type=repository`. ArgoCD
auto-discovers repository secrets by this label.

```bash
kubectl create secret generic repo-kubeauto \
  --namespace argocd \
  --from-literal=type=git \
  --from-literal=url=https://github.com/peopleforrester/kubeauto-ai-day.git \
  --from-literal=username=git \
  --from-literal=password=<GITHUB_PAT>
kubectl label secret repo-kubeauto -n argocd \
  argocd.argoproj.io/secret-type=repository
```

### Sync Waves (1 correction cycle)

**Problem: Drift detection test checked wrong field.**
The test added a label to a namespace and expected ArgoCD to revert it.
But annotation-based tracking (ArgoCD 3.x default) only monitors fields
that ArgoCD manages. A new label added by kubectl is not a managed field.

*Fix:* Changed the test to modify an existing managed field (an existing
label value) instead of adding a new label. ArgoCD correctly detects and
reverts changes to fields it manages.

---

## Phase 3: Security Stack

### Kyverno Install (3 correction cycles)

**Problem 1: Webhook config format wrong.**
The skill file showed webhook namespaceSelector as a list, but chart 3.7.0
expects a map structure under `config.webhooks.namespaceSelector`.

*Fix:* Changed from list format to map format:
```yaml
# WRONG (skill file had this)
webhooks:
  - namespaceSelector:
      matchExpressions: [...]

# CORRECT (chart 3.7.0 expects this)
config:
  webhooks:
    namespaceSelector:
      matchExpressions: [...]
```

**Problem 2: CRD annotation too large for client-side apply.**
Kyverno CRDs have very large `kubectl.kubernetes.io/last-applied-configuration`
annotations that exceed the 256KB annotation limit. `kubectl apply` fails.

*Fix:* Added `ServerSideApply=true` to the ArgoCD Application syncOptions.
Server-side apply doesn't use the last-applied-configuration annotation.

**Problem 3: Stale sync after fix.**
After fixing the webhook config, ArgoCD showed the Application as Synced
but the old (broken) resources were still in the cluster. ArgoCD's cache
was stale.

*Fix:* Force-refreshed the Application:
```bash
kubectl patch application kyverno -n argocd \
  --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'
```

### Falco Install (2 correction cycles)

**Problem 1: Wrong chart version in skill file.**
The skill file referenced chart version `4.x` which maps to Falco 0.37.x.
The current chart was `7.x` (at the time) mapping to Falco 0.42.x.

*Fix:* Updated to chart 7.2.1, then later bumped to 8.0.0 (Falco 0.43.0)
during the version audit.

**Problem 2: `write_etc_common` macro removed.**
The custom Falco rule for "Write Below Etc in Container" used the
`write_etc_common` macro which was removed in Falco 0.42.x. Rule loading
failed silently (Falco started but the rule didn't fire).

*Fix:* Replaced `write_etc_common` with inline conditions:
```yaml
condition: >
  evt.dir = < and
  fd.name startswith /etc/ and
  container and
  not proc.name in (sed, tee) and
  not k8s.ns.name in (kube-system, kyverno, argocd, monitoring, security)
```

### Falco Version Bump 7.2.1 → 8.0.0 (3 additional correction cycles)

**Problem 1: gRPC output deprecated.**
Chart 8.0.0 (Falco 0.43.0) deprecated gRPC output in favor of HTTP.
The initial config used `grpc_output` which silently did nothing.

*Fix:* Switched to HTTP output:
```yaml
falco:
  http_output:
    enabled: true
    url: "http://falcosidekick.security.svc.cluster.local:2801"
```

**Problem 2: Wrong Falcosidekick service name.**
Set the URL to `falco-falcosidekick.security.svc.cluster.local` but the
actual service name is just `falcosidekick` (no release-name prefix).
DNS resolution failed: `libcurl failed to perform call: Couldn't resolve host name`.

*Fix:* Changed URL to `falcosidekick.security.svc.cluster.local`.

**Problem 3: Chart template overrides manual URL.**
Even after fixing the URL in `falco.http_output.url`, the Falco chart's
Helm template computed its own URL as `<release-name>-falcosidekick` and
overrode the manual setting. The chart ignores the URL field when it
detects Falcosidekick config.

*Fix:* Used `falcosidekick.fullfqdn` which is the chart's mechanism for
specifying an external Falcosidekick URL:
```yaml
falcosidekick:
  enabled: false
  fullfqdn: falcosidekick.security.svc.cluster.local
```

### ESO + Secrets Manager (2 correction cycles)

**Problem 1: API version v1beta1 → v1.**
ESO 1.3.2 uses `apiVersion: external-secrets.io/v1` for ExternalSecret
and ClusterSecretStore resources. The AI generated `v1beta1` which is
the old API version from ESO 0.x.

*Fix:* Changed all ESO resource manifests from `v1beta1` to `v1`.

**Problem 2: ArgoCD sync cache stale after API version fix.**
After fixing the API version, ArgoCD still tried to apply the old
`v1beta1` manifests because its cache hadn't refreshed.

*Fix:* Hard refresh:
```bash
kubectl patch application eso-resources -n argocd \
  --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'
```

*Pattern:* Any time you fix a CRD API version mismatch, you MUST hard-refresh
the ArgoCD Application. ArgoCD caches the discovered API versions.

---

## Phase 4: Observability

### OTel Collector (3 correction cycles)

**Problem 1: Chart 0.145.0 requires explicit image.repository.**
Breaking change from chart 0.89+: the `image.repository` field is no
longer defaulted. Without it, the chart pulls a generic image that may
not match the expected architecture.

*Fix:* Added explicit image repository:
```yaml
image:
  repository: "otel/opentelemetry-collector-contrib"
```

**Problem 2: `k8s` image lacks prometheusremotewrite exporter.**
The default `otel/opentelemetry-collector-k8s` image does NOT include the
`prometheusremotewrite` exporter. Pipeline startup fails with
"exporter prometheusremotewrite not found." This is not documented in
the chart — you only discover it at runtime.

*Fix:* Changed to `otel/opentelemetry-collector-contrib` which includes
all exporters. The `contrib` image is larger but has everything.

**Problem 3: DaemonSet mode disables ClusterIP service.**
When `mode: daemonset`, the chart does NOT create a ClusterIP Service by
default. Applications sending OTLP to
`otel-collector-opentelemetry-collector.monitoring:4317` get DNS failures.

*Fix:* Explicitly enabled the service:
```yaml
service:
  enabled: true
  type: ClusterIP
```

### Prometheus + Grafana (1 correction cycle)

**Problem: kubectl run stdout noise.**
A test ran `kubectl run` to execute a curl command and captured stdout.
The pod deletion message ("pod deleted") was appended to the JSON output,
making JSON parsing fail.

*Fix:* Stripped the deletion message from stdout before parsing, or used
`--rm=false` and cleaned up separately.

---

## Phase 5: Developer Portal

### Backstage Install (1 correction cycle)

**Problem: Kyverno livenessProbe validation in dry-run test.**
The test did a `kubectl apply --dry-run=server` of a Backstage-templated
resource. Kyverno's webhook intercepted the dry-run and rejected it
because the resource's livenessProbe didn't match the expected format
for the `require-probes` policy.

*Fix:* Ensured the Backstage template skeleton includes both
`readinessProbe` and `livenessProbe` with `httpGet` format matching
what Kyverno expects.

### Private Repo Catalog Access

**Problem: Backstage couldn't read catalog from private GitHub repo.**
The default `app-config.yaml` catalog location uses `url:` type which
requires GitHub token auth. For a private repo, this requires configuring
GitHub integration in Backstage.

*Fix:* Used a ConfigMap-based catalog approach instead. Mounted catalog
YAML files via a ConfigMap volume, and pointed Backstage's `catalog.locations`
to local file paths (`file:///catalog/*.yaml`). This avoids GitHub auth
entirely for the catalog.

---

## Phase 6: Integration Testing

### E2E Sample App Test (2 correction cycles)

**Problem 1: NetworkPolicy blocks pod-to-service egress.**
The test ran `wget` from a busybox pod to `sample-app.apps.svc:8080`.
The `default-deny-all` NetworkPolicy blocks all egress from the apps
namespace except DNS (port 53 to kube-system) and ingress from
kube-system. Pod-to-service within the same namespace is blocked.

*Fix:* Changed the test to exec into the sample-app pod itself and
use `urllib` to hit `localhost:8080/health`. No network policy blocks
localhost traffic.

**Problem 2: Falco non-interactive exec not detected.**
The test ran `kubectl exec ... -- sh -c "echo falco-integration-test"`
and expected Falco to log it. But Falco's "Exec Into Pod" rule requires
a TTY-attached shell spawned by a container runtime. Non-interactive
`sh -c` without TTY doesn't match the rule conditions.

*Fix:* Changed the test to `kubectl exec ... -- sh -c "touch /etc/falco-integration-marker"`.
This triggers the "Write Below Etc in Container" rule instead, which
detects any file write under `/etc/` in a container. The marker filename
is unique and searchable in Falco logs.

### ArgoCD Drift Detection Test

**Problem: Label addition vs modification.**
Same issue as Phase 2 — adding a new label isn't detected as drift by
annotation-based tracking. Modified the test to change an existing
managed field.

---

## Phase 7: Production Hardening

### cert-manager (1 correction cycle)

**Problem: Application YAML in subdirectory.**
Initially created the cert-manager Application YAML at
`gitops/apps/cert-manager/application.yaml` (in a subdirectory).
The app-of-apps root points to `gitops/apps/` with no recursion.
ArgoCD only reads YAML files in the top-level directory.

*Fix:* Moved to `gitops/apps/cert-manager.yaml` (top-level). Created
a separate `gitops/apps/cert-manager-issuers.yaml` for the ClusterIssuers.

**Critical rule: The app-of-apps directory does NOT recurse into
subdirectories.** All Application manifests must be at the top level
of `gitops/apps/`.

### cert-manager Namespace Ordering

**Problem: cert-manager namespace didn't exist yet.**
cert-manager Application (sync wave -5) tried to deploy before the
namespaces Application (sync wave -10) had finished creating the
`cert-manager` namespace.

*Fix:* Added `cert-manager` to `gitops/namespaces/namespaces.yaml` and
force-refreshed the namespaces Application. The sync wave ordering then
handled the dependency correctly.

### gitleaks False Positive

**Problem: Test secret detected.**
`gitleaks detect` found `testpass123` in `infrastructure/terraform/secrets.tf`
(the ESO validation secret created in Phase 3).

*Fix:* Created `.gitleaks.toml` allowlist:
```toml
[allowlist]
  description = "Known test secrets for ESO validation"
  commits = ["0dad4b85ea22a99e68d3853e448104931240fe39"]
  paths = ["infrastructure/terraform/secrets.tf"]
```

---

## Cross-Cutting Lessons

### 1. ArgoCD Hard Refresh is Your Friend
Any time you change CRD API versions, fix Helm values, or modify sync
options, force a hard refresh. ArgoCD's cache aggressively caches API
discovery and manifest state.

### 2. Skill Files Prevent Repeat Mistakes
The `.claude/skills/` files were the single biggest factor in reducing
correction cycles. When the skill file was wrong (Falco chart version,
Kyverno webhook format), it caused a correction. When correct, components
deployed first try.

### 3. Version Currency is AI's Achilles Heel
Every "Partial" toil-shift component (5/26) was caused by stale version
knowledge: wrong chart version, deprecated API, removed macro, breaking
image change. Pin exact versions in your prompts and skill files.

### 4. TDD Catches Everything Fast
The 5-step TDD cycle (write test → confirm failure → implement → confirm
pass → refactor) meant every mistake was caught within minutes. Without
tests, the Falco macro removal or OTel image issue could have burned hours.

### 5. Helm Chart Templates Override Values
Some Helm charts compute values internally that override what you set in
`values.yaml`. Falco's Falcosidekick URL is the prime example. When
debugging "my value isn't taking effect," check the chart's templates.

### 6. NetworkPolicy Blocks More Than You Think
The `default-deny-all` egress policy in `apps` namespace blocks pod-to-service
traffic within the same namespace. Only DNS (port 53) and traffic from
kube-system ingress controllers are allowed. Plan your test strategies
around this.

### 7. ServerSideApply for Large CRDs
Any CRD-heavy operator (Kyverno, Prometheus, cert-manager) should use
`ServerSideApply=true` in ArgoCD syncOptions. The `last-applied-configuration`
annotation from client-side apply can exceed the 256KB limit.

### 8. Don't Sanitize Live Deployment Files
Replacing AWS account IDs with `<AWS_ACCOUNT_ID>` placeholders for public
release MUST happen at publish time — not while the cluster is live. ArgoCD
syncs from the repo, so sanitized files get deployed and break image pulls.
The pre-flight checklist in SETUP.md documents the reverse: replacing
placeholders with your real account ID before deploying.
