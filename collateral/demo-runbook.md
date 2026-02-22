# ABOUTME: Demo runbook for live KubeAuto Day presentation.
# ABOUTME: Step-by-step commands to demonstrate each platform component.

# KubeAuto Day IDP Demo Runbook

Pre-requisites:
- `kubectl` configured with cluster context
- `argocd` CLI logged in (or use UI)
- Browser open to ArgoCD, Grafana, Backstage UIs

---

## 1. Platform Health Check (2 min)

```bash
# Show all namespaces
kubectl get namespaces

# Show all ArgoCD applications
kubectl get applications -n argocd

# Quick health summary
kubectl get pods --all-namespaces | grep -v Running | grep -v Completed
```

**Talking point:** "Every component you see here was deployed by ArgoCD from Git.
No kubectl apply was used after the bootstrap."

---

## 2. GitOps: ArgoCD App-of-Apps (3 min)

```bash
# Show the root application
kubectl get application app-of-apps -n argocd -o yaml | head -30

# Show all child applications managed by the root app
kubectl get applications -n argocd -o custom-columns=NAME:.metadata.name,SYNC:.status.sync.status,HEALTH:.status.health.status

# Show the gitops directory structure
ls -la gitops/apps/
```

**Talking point:** "One root Application watches gitops/apps/. Drop a YAML
file in that directory, push to Git, and ArgoCD deploys it. That's the entire
deployment workflow."

---

## 3. Drift Detection + Self-Heal (2 min)

```bash
# Show current service state
kubectl get service sample-app -n apps -o jsonpath='{.spec.ports[0].name}'
echo

# Introduce drift by modifying a managed field
kubectl patch service sample-app -n apps \
  --type=json -p '[{"op":"replace","path":"/spec/ports/0/name","value":"drifted"}]'

# Verify the drift
kubectl get service sample-app -n apps -o jsonpath='{.spec.ports[0].name}'
echo

# Wait 30s for ArgoCD self-heal (reconciliation interval is 30s)
echo "Waiting for ArgoCD to self-heal..."
sleep 35

# Confirm ArgoCD reverted the change
kubectl get service sample-app -n apps -o jsonpath='{.spec.ports[0].name}'
echo
```

**Talking point:** "ArgoCD detects the drift and reverts it within 30 seconds.
This is annotation-based tracking — it knows exactly which fields it manages."

---

## 4. Policy Enforcement: Kyverno (3 min)

```bash
# Show active policies
kubectl get clusterpolicies

# Try to deploy a non-compliant pod (no resources, no probes, latest tag)
kubectl run bad-pod --image=nginx:latest -n apps --dry-run=server

# Expected: Kyverno blocks with specific policy violations

# Show what a compliant pod looks like
kubectl get deployment sample-app -n apps -o yaml | grep -A 20 'containers:'
```

**Talking point:** "Kyverno enforces 6 policies in the apps namespace:
resource limits, probes, non-root, no latest tag, no privilege escalation,
and capabilities drop ALL. System namespaces are excluded."

---

## 5. Runtime Security: Falco (2 min)

```bash
# Show Falco is running on every node (DaemonSet)
kubectl get pods -n security -l app.kubernetes.io/name=falco

# Trigger a detectable event: exec a shell into a running pod
POD=$(kubectl get pods -n apps -l app=sample-app -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n apps $POD -- sh -c "echo 'Falco should detect this shell exec'"

# Check Falco logs for the alert (wait 5s for async processing)
sleep 5
kubectl logs -n security -l app.kubernetes.io/name=falco -c falco --tail=20 --since=15s | grep -i "exec\|shell\|terminal"
```

**Talking point:** "Falco uses eBPF to detect syscall-level events in real time.
Spawning a shell in a container triggers an alert immediately. We also detect
writes to /etc, EC2 metadata access, and crypto mining activity."

**If no alert shows:** Check `--since=30s` or `--tail=100` — Falco processes
events asynchronously and high-volume pods may push logs further back.

---

## 6. Secrets Management: ESO (2 min)

```bash
# Show the ClusterSecretStore
kubectl get clustersecretstore -n platform

# Show the ExternalSecret and synced Secret
kubectl get externalsecret -n apps
kubectl get secret kubeauto-test-secret -n apps -o jsonpath='{.data.test-key}' | base64 -d
echo
```

**Talking point:** "External Secrets Operator syncs secrets from AWS Secrets
Manager. The secret value never appears in Git — only the reference does."

---

## 7. Observability Stack (3 min)

```bash
# Show Prometheus scrape targets
kubectl run prom-check --rm -i --restart=Never \
  --image=busybox:latest -n monitoring -- \
  wget -q -O- --timeout=5 \
  'http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090/api/v1/targets' \
  | python3 -c "import sys,json; targets=json.load(sys.stdin)['data']['activeTargets']; print(f'{len(targets)} active scrape targets')"

# Show OTel Collector is forwarding metrics
kubectl get pods -n monitoring -l app.kubernetes.io/name=opentelemetry-collector

# Show custom alert rules
kubectl get prometheusrules -n monitoring
```

**Talking point:** "kube-prometheus-stack provides Prometheus, Grafana, and
alerting. OTel Collector runs as a DaemonSet forwarding metrics via remote
write. We have 4 custom alert rules for production scenarios."

**Open Grafana UI:** Navigate to the Platform Overview dashboard.

---

## 8. Developer Portal: Backstage (3 min)

```bash
# Show Backstage is running
kubectl get pods -n backstage

# Query the catalog API
kubectl run bs-check --rm -i --restart=Never \
  --image=busybox:latest -n backstage -- \
  wget -q -O- --timeout=5 \
  'http://backstage.backstage.svc.cluster.local:7007/api/catalog/entities?filter=kind=component'

# Show software templates available
kubectl run bs-templates --rm -i --restart=Never \
  --image=busybox:latest -n backstage -- \
  wget -q -O- --timeout=5 \
  'http://backstage.backstage.svc.cluster.local:7007/api/catalog/entities?filter=kind=template'
```

**Talking point:** "Backstage provides a single pane of glass for the platform.
Developers see their services, deploy new ones via templates, and the templates
produce Kyverno-compliant resources by default."

**Open Backstage UI:** Show catalog, component, and template pages.

---

## 9. Template Validation (2 min)

```bash
# Show the template skeleton deployed as a real service
kubectl get deployment templated-test-svc -n apps
kubectl get pods -n apps -l app=templated-test-svc

# Verify it passed Kyverno
kubectl run kyverno-check --image=nginx:1.27 -n apps --dry-run=server \
  --overrides='{"spec":{"securityContext":{"runAsNonRoot":true,"runAsUser":1000,"fsGroup":1000},"containers":[{"name":"check","image":"nginx:1.27","ports":[{"containerPort":8080}],"resources":{"requests":{"cpu":"100m","memory":"128Mi"},"limits":{"cpu":"500m","memory":"256Mi"}},"readinessProbe":{"httpGet":{"path":"/","port":8080},"initialDelaySeconds":5},"livenessProbe":{"httpGet":{"path":"/","port":8080},"initialDelaySeconds":10},"securityContext":{"allowPrivilegeEscalation":false,"capabilities":{"drop":["ALL"]}}}]},"metadata":{"labels":{"app":"check","version":"v1.0.0"}}}'
```

**Talking point:** "The template skeleton produces resources that are
Kyverno-compliant by default. Developers can't accidentally deploy
non-compliant workloads."

---

## 10. Full Integration Test (1 min)

```bash
# Run the automated integration test suite
uv run pytest tests/test_phase_06_integration.py -v
```

**Talking point:** "59 automated tests validate every component, from Terraform
state to Falco detection to ArgoCD self-healing. All tests hit real
infrastructure — no mocks."

---

## Known Issues

| Issue | Symptom | Workaround |
|-------|---------|------------|
| ArgoCD drift detection timing | Self-heal takes up to 30s (reconciliation interval) | Start the drift demo early, talk through it while waiting |
| Falco alert delay | Alerts appear in logs 2-10s after the event | Add `sleep 5` before checking logs; check `--since=30s` |
| Falcosidekick event lag | Metrics may not immediately reflect new events | Check `--tail=200` instead of `--tail=10` for recent alerts |
| app-of-apps OutOfSync | Root app often shows OutOfSync while children are Synced | This is normal for app-of-apps pattern; all child apps are Healthy |
| Kyverno OutOfSync | Kyverno app shows OutOfSync in ArgoCD | CRD size exceeds annotation limits; Kyverno is Healthy regardless |
| Backstage catalog load | Catalog entities take ~20s to load after pod restart | Wait for pod to be Ready before querying catalog API |
| Grafana initial dashboard load | First load may show "No data" briefly | Refresh the dashboard; Prometheus needs a few scrape intervals |

**If something fails live:**
- Stay calm, acknowledge it: "This is real infrastructure, not a rehearsed recording"
- Check pod status: `kubectl get pods -n <namespace>`
- Check pod logs: `kubectl logs -n <namespace> <pod> --tail=20`
- Skip to next demo section and come back if time allows
- The test suite is your safety net: `uv run pytest tests/test_phase_06_integration.py -v`

---

## Quick Reference

### External URLs (Browser)

| Service | URL |
|---------|-----|
| ArgoCD | https://test1.ai-enhanced-devops.com |
| Backstage | https://backstage.ai-enhanced-devops.com |
| Unicorn Party | https://unicorn.ai-enhanced-devops.com |
| E-Commerce Demo | https://ecom.ai-enhanced-devops.com |

### Internal URLs (kubectl)

| Service | Namespace | Internal URL |
|---------|-----------|--------------|
| ArgoCD UI | argocd | https://argocd-server.argocd.svc:443 |
| Grafana | monitoring | http://prometheus-grafana.monitoring.svc:80 |
| Prometheus | monitoring | http://prometheus-kube-prometheus-prometheus.monitoring.svc:9090 |
| Backstage | backstage | http://backstage.backstage.svc:7007 |
| Sample App | apps | http://sample-app.apps.svc:8080 |
| Falcosidekick | security | http://falco-falcosidekick.security.svc:2801 |

### Credentials

| Service | Credentials |
|---------|-------------|
| Grafana | admin / admin |
| ArgoCD | GitHub OIDC (peopleforrester, WiggityWhitney) |
| Backstage | GitHub OIDC (peopleforrester, WiggityWhitney) |
