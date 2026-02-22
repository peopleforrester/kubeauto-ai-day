# Observability

Grafana dashboards and visualization resources. The core observability stack
(Prometheus, Grafana, OTel Collector, Tempo, Loki, Promtail) is deployed via
ArgoCD Application manifests in `gitops/apps/`.

## Directory Structure

```
grafana/
  dashboards/
    platform-overview.yaml   # ConfigMap with Platform Overview dashboard JSON
```

## Observability Stack

| Component | Purpose | Deployed Via |
|-----------|---------|-------------|
| Prometheus | Metrics collection + alerting | `gitops/apps/prometheus.yaml` (kube-prometheus-stack 82.1.0) |
| Grafana | Dashboards + visualization | Bundled with kube-prometheus-stack |
| OTel Collector | Trace/metric pipeline | `gitops/apps/otel-collector.yaml` (contrib 0.145.0) |
| Tempo | Distributed tracing backend | `gitops/apps/tempo.yaml` |
| Loki | Log aggregation | `gitops/apps/loki.yaml` |
| Promtail | Log shipping | `gitops/apps/promtail.yaml` |

## Data Flow

```
Apps → OTel Collector → Tempo (traces)
                      → Prometheus (metrics via remote write)
Apps → Promtail → Loki (logs)
Prometheus ← scrape ← ServiceMonitors (metrics)
Grafana ← query ← Prometheus + Tempo + Loki
```

## Dashboards

The Platform Overview dashboard is provisioned automatically via Grafana's
sidecar. Any ConfigMap with the label `grafana_dashboard: "1"` in any
namespace is picked up and loaded.

## Alert Rules

Four custom PrometheusRules are defined inline in the kube-prometheus-stack
values (`gitops/apps/prometheus.yaml`):

| Alert | Severity | Condition |
|-------|----------|-----------|
| NodeNotReady | Critical | Node not ready for 5 min |
| PodCrashLoop | Warning | 3+ restarts in 10 min |
| ArgoCDAppDegraded | Warning | App degraded for 5 min |
| FalcoCriticalAlert | Critical | Falco critical event detected |

See [ADR-005](../docs/adr/ADR-005-observability-stack.md) for stack selection rationale.
