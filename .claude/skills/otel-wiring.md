# OTel Collector Wiring — Skill File

## Version

OTel Collector **0.140+** (still 0.x, no GA release yet). The configuration format is stable despite the 0.x version. Pin to a specific 0.14x release in Helm values to avoid surprises.

---

## Architecture

The OTel Collector runs as a **DaemonSet** on each node. It receives telemetry data (metrics, traces, logs) from applications via OTLP protocol, processes it, and exports it to backends.

```
Flask App (OTel SDK) --OTLP--> OTel Collector --prometheusremotewrite--> Prometheus
                                              \--otlp/jaeger-----------> (traces backend)
```

The collector config has four top-level sections:
1. **receivers** — how data enters the collector
2. **processors** — transformations and filtering applied to data
3. **exporters** — where data is sent after processing
4. **service.pipelines** — wiring that connects receivers -> processors -> exporters

---

## Correct Patterns

### OTel Collector Config (observability/otel-collector/config.yaml)

```yaml
# ABOUTME: OpenTelemetry Collector configuration for the KubeAuto Day IDP
# ABOUTME: Receives OTLP telemetry, processes it, exports metrics to Prometheus

receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

  # Scrape the collector's own metrics
  prometheus:
    config:
      scrape_configs:
        - job_name: otel-collector
          scrape_interval: 10s
          static_configs:
            - targets:
                - 0.0.0.0:8888

processors:
  # Batch processor: groups data before exporting for efficiency
  batch:
    timeout: 5s
    send_batch_size: 1024
    send_batch_max_size: 2048

  # Memory limiter: prevents collector OOM
  # MUST be the first processor in every pipeline
  memory_limiter:
    check_interval: 1s
    limit_mib: 400
    spike_limit_mib: 100

  # Add Kubernetes metadata to telemetry
  resource:
    attributes:
      - key: cluster.name
        value: kubeauto-eks
        action: upsert

exporters:
  # Export metrics to Prometheus via remote write
  prometheusremotewrite:
    endpoint: http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090/api/v1/write
    tls:
      insecure: true
    resource_to_telemetry_conversion:
      enabled: true

  # Debug exporter for troubleshooting (writes to collector stdout)
  debug:
    verbosity: basic
    sampling_initial: 5
    sampling_thereafter: 200

  # OTLP exporter for traces (to a trace backend if configured)
  # Uncomment if Jaeger or Tempo is deployed
  # otlp/traces:
  #   endpoint: tempo.monitoring.svc.cluster.local:4317
  #   tls:
  #     insecure: true

service:
  # Collector telemetry (self-monitoring)
  telemetry:
    logs:
      level: info
    metrics:
      address: 0.0.0.0:8888

  pipelines:
    # Metrics pipeline: OTLP in -> process -> Prometheus remote write out
    metrics:
      receivers:
        - otlp
        - prometheus
      processors:
        - memory_limiter    # MUST be first
        - batch
        - resource
      exporters:
        - prometheusremotewrite
        - debug

    # Traces pipeline: OTLP in -> process -> debug out (or OTLP out)
    traces:
      receivers:
        - otlp
      processors:
        - memory_limiter    # MUST be first
        - batch
        - resource
      exporters:
        - debug
        # - otlp/traces     # Uncomment when trace backend is available
```

### ArgoCD Application (gitops/apps/otel-collector/application.yaml)

```yaml
# ABOUTME: ArgoCD Application for the OpenTelemetry Collector
# ABOUTME: Deploys OTel Collector DaemonSet to monitoring namespace
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: otel-collector
  namespace: argocd
  annotations:
    argocd.argoproj.io/sync-wave: "4"
spec:
  project: default
  source:
    repoURL: https://open-telemetry.github.io/opentelemetry-helm-charts
    chart: opentelemetry-collector
    targetRevision: "0.108.*"   # Helm chart version (NOT collector version)
    helm:
      valuesObject:
        mode: daemonset
        presets:
          kubernetesAttributes:
            enabled: true
        config:
          # Inline the config from observability/otel-collector/config.yaml
          # OR use a ConfigMap reference
        resources:
          requests:
            cpu: 100m
            memory: 256Mi
          limits:
            cpu: 500m
            memory: 512Mi
        ports:
          otlp:
            enabled: true
            containerPort: 4317
            servicePort: 4317
            protocol: TCP
          otlp-http:
            enabled: true
            containerPort: 4318
            servicePort: 4318
            protocol: TCP
          metrics:
            enabled: true
            containerPort: 8888
            servicePort: 8888
            protocol: TCP
  destination:
    server: https://kubernetes.default.svc
    namespace: monitoring
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=false
```

### Flask App OTel Auto-Instrumentation (sample-app/k8s/deployment.yaml excerpt)

The sample Flask app uses OTel auto-instrumentation. The environment variables tell the OTel SDK where to send data:

```yaml
# Relevant container env vars for OTel auto-instrumentation
env:
  # OTLP endpoint — the OTel Collector service in the monitoring namespace
  - name: OTEL_EXPORTER_OTLP_ENDPOINT
    value: "http://otel-collector-opentelemetry-collector.monitoring.svc.cluster.local:4317"
  # Protocol: gRPC (default for OTLP)
  - name: OTEL_EXPORTER_OTLP_PROTOCOL
    value: "grpc"
  # Service name for traces and metrics
  - name: OTEL_SERVICE_NAME
    value: "sample-app"
  # Resource attributes
  - name: OTEL_RESOURCE_ATTRIBUTES
    value: "service.namespace=apps,deployment.environment=production"
  # Enable trace propagation
  - name: OTEL_PROPAGATORS
    value: "tracecontext,baggage"
  # Metrics export interval (milliseconds)
  - name: OTEL_METRIC_EXPORT_INTERVAL
    value: "10000"
```

For Python Flask with auto-instrumentation, the Dockerfile CMD uses `opentelemetry-instrument`:

```dockerfile
# In sample-app/Dockerfile
RUN pip install opentelemetry-distro opentelemetry-exporter-otlp
RUN opentelemetry-bootstrap -a install

CMD ["opentelemetry-instrument", "flask", "run", "--host=0.0.0.0", "--port=8080"]
```

Or in the Python requirements:

```
opentelemetry-distro
opentelemetry-exporter-otlp-proto-grpc
opentelemetry-instrumentation-flask
opentelemetry-instrumentation-requests
```

### Prometheus Remote Write — Enabling the Receiver

For `prometheusremotewrite` exporter to work, Prometheus must have remote write receiver enabled. In kube-prometheus-stack Helm values:

```yaml
# In observability/prometheus/values.yaml
prometheus:
  prometheusSpec:
    enableRemoteWriteReceiver: true
    # The remote write receiver listens on the same port as Prometheus (9090)
    # at path /api/v1/write
```

---

## Guardrail Integration

The OTel Collector + Prometheus + Grafana stack implements **Guardrail #5** at Layer 3 (Kubernetes Infrastructure).

| Guardrail | How Observability Implements It |
|-----------|-------------------------------|
| **#5 Immutable Audit Trail** | Distributed traces link requests across services. Prometheus metrics provide time-series audit data. Grafana dashboards make the audit trail queryable and visual. Custom alert rules (NodeNotReady, PodCrashLoop, ArgoCDAppDegraded, FalcoCriticalAlert) provide active monitoring of the audit trail. |

**The observability stack makes all other guardrails auditable.** Without metrics and traces, you know policies exist but not whether they're firing. With OTel, every Kyverno rejection, Falco alert, and ArgoCD sync event becomes a data point.

**Layer 2 enforcement:** The `cc-posttool-audit.sh` hook reminds operators to verify deployments after applying changes — the observability stack is what makes that verification possible.

---

### ServiceMonitor for OTel Collector Self-Metrics

```yaml
# ABOUTME: ServiceMonitor for Prometheus to scrape OTel Collector self-metrics
# ABOUTME: Enables monitoring of the collector's health and throughput
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: otel-collector
  namespace: monitoring
  labels:
    release: prometheus    # Must match kube-prometheus-stack release label
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: opentelemetry-collector
  endpoints:
    - port: metrics
      interval: 15s
      path: /metrics
```

---

## Common Mistakes

### Mistake 1: Wrong Prometheus remote write endpoint

```yaml
# WRONG — service name doesn't match actual Prometheus service
exporters:
  prometheusremotewrite:
    endpoint: http://prometheus:9090/api/v1/write
```

Fix: The actual service name depends on how kube-prometheus-stack was installed. Verify with:
```bash
kubectl get svc -n monitoring | grep prometheus
```
The typical full service name is:
`http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090/api/v1/write`

**This is the number one cause of silent data loss.** Always verify the endpoint matches an actual service.

### Mistake 2: memory_limiter not first in processor chain

```yaml
# WRONG — batch before memory_limiter risks OOM
pipelines:
  metrics:
    processors:
      - batch
      - memory_limiter    # Too late — OOM can happen during batching
```

Fix: `memory_limiter` MUST be the first processor in every pipeline. It prevents the collector from running out of memory by dropping data when approaching the limit.

### Mistake 3: Using prometheus exporter instead of prometheusremotewrite

```yaml
# WRONG — prometheus exporter creates a /metrics endpoint for scraping
# It does NOT push to Prometheus
exporters:
  prometheus:
    endpoint: 0.0.0.0:8889
```

The `prometheus` exporter exposes a scrape endpoint. The `prometheusremotewrite` exporter pushes data to Prometheus. For this project, we want remote write (push model) so OTel-collected metrics appear in Prometheus alongside scraped metrics.

### Mistake 4: Port mismatch between app and collector

```yaml
# WRONG — app sends to 4317 but collector listens on different port
# In the app:
OTEL_EXPORTER_OTLP_ENDPOINT: "http://otel-collector:4318"
OTEL_EXPORTER_OTLP_PROTOCOL: "grpc"
```

Fix: gRPC uses port **4317**. HTTP uses port **4318**. If the protocol is `grpc`, the endpoint must use port 4317. If the protocol is `http/protobuf`, use port 4318. Mismatched port/protocol is a silent failure — no errors, just no data.

### Mistake 5: Missing Prometheus remote write receiver

```yaml
# WRONG — Prometheus doesn't accept remote write by default
# No enableRemoteWriteReceiver in prometheus values
```

Fix: Set `prometheus.prometheusSpec.enableRemoteWriteReceiver: true` in kube-prometheus-stack values. Without this, the collector's remote write exports will fail with connection refused or 404.

### Mistake 6: Using OTEL_EXPORTER_OTLP_ENDPOINT with scheme for gRPC

```yaml
# WRONG for gRPC — some SDKs don't want http:// prefix for gRPC
OTEL_EXPORTER_OTLP_ENDPOINT: "http://collector:4317"
OTEL_EXPORTER_OTLP_PROTOCOL: "grpc"
```

For Python OTel SDK, the `http://` prefix is actually required even for gRPC. However, for Go and some other SDKs, omit the scheme for gRPC. Since our sample app is Python Flask, `http://` is correct. Be careful when copying patterns across languages.

### Mistake 7: Collector Helm chart version vs collector version

The Helm chart version (e.g., `0.108.x`) is NOT the same as the collector binary version (e.g., `0.140.x`). The chart version increments independently. Always check the chart's `appVersion` to know which collector version it deploys:

```bash
helm show chart open-telemetry/opentelemetry-collector --version 0.108.0 | grep appVersion
```

### Mistake 8: Not setting resource_to_telemetry_conversion

```yaml
# WRONG — resource attributes won't appear as metric labels
exporters:
  prometheusremotewrite:
    endpoint: http://prometheus:9090/api/v1/write
    # Missing resource_to_telemetry_conversion
```

Fix: Set `resource_to_telemetry_conversion.enabled: true` so that OTel resource attributes (like `service.name`, `k8s.namespace.name`) become Prometheus metric labels. Without this, metrics in Prometheus lack identifying information.

---

## Validation Commands

```bash
# Verify OTel Collector DaemonSet is running
kubectl get ds -n monitoring -l app.kubernetes.io/name=opentelemetry-collector
# Pod count should match node count

# Verify collector pods are ready
kubectl get pods -n monitoring -l app.kubernetes.io/name=opentelemetry-collector

# Check collector logs for errors
kubectl logs -n monitoring -l app.kubernetes.io/name=opentelemetry-collector --tail=30
# Look for: "Everything is ready" or pipeline start messages
# Red flags: "connection refused", "context deadline exceeded", "dropping data"

# Verify OTLP gRPC receiver is listening
kubectl port-forward -n monitoring svc/otel-collector-opentelemetry-collector 4317:4317 &
# Send a test span via grpcurl or check with:
# grpcurl -plaintext localhost:4317 list

# Verify OTLP HTTP receiver is listening
curl -s -o /dev/null -w "%{http_code}" http://localhost:4318/v1/traces
# Should return 200 or 405 (method not allowed for GET, but proves it's listening)

# Check collector self-metrics
kubectl port-forward -n monitoring svc/otel-collector-opentelemetry-collector 8888:8888 &
curl -s http://localhost:8888/metrics | head -20
# Should see otelcol_receiver_accepted_spans, otelcol_exporter_sent_metric_points, etc.

# Verify Prometheus remote write endpoint is reachable FROM the collector
kubectl exec -n monitoring -l app.kubernetes.io/name=opentelemetry-collector -- \
  wget -q -O- http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090/-/ready
# Should return "Prometheus Server is Ready."

# Verify Prometheus remote write receiver is enabled
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090 &
curl -s -X POST http://localhost:9090/api/v1/write
# Should return 400 (bad request) not 404 (not found)
# 404 means remote write receiver is NOT enabled

# Verify metrics are flowing: check for OTel-originated metrics in Prometheus
curl -s "http://localhost:9090/api/v1/query?query=up" | python3 -m json.tool | head -20

# Check that sample app's OTel env vars are set correctly
kubectl get deployment -n apps sample-app -o jsonpath='{.spec.template.spec.containers[0].env}' | python3 -m json.tool

# Verify sample app is sending telemetry (check collector logs for received data)
kubectl logs -n monitoring -l app.kubernetes.io/name=opentelemetry-collector --tail=20 | grep -i "sample-app"

# End-to-end trace test: hit the sample app and check for spans
curl http://sample-app.apps.svc.cluster.local:8080/
# Then check collector logs:
kubectl logs -n monitoring -l app.kubernetes.io/name=opentelemetry-collector --tail=10
# Should see trace/span data being received and exported

# Verify the full pipeline: app -> collector -> prometheus
# Query Prometheus for a metric that should come from OTel
curl -s "http://localhost:9090/api/v1/query?query=http_server_request_duration_seconds_count" | python3 -m json.tool
# Should return results if the Flask app has received any HTTP requests
```
