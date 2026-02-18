# ADR-005: Observability Stack

## Status

Accepted

## Context

The IDP needs full-stack observability covering metrics, traces, and
alerting. The solution must be CNCF-native, open source, and integrate
with our existing ArgoCD GitOps workflow.

## Decision

Use the **CNCF-native observability stack**:
- **Prometheus** (metrics collection and alerting)
- **Grafana 12.x** (visualization and dashboards)
- **OpenTelemetry Collector** (telemetry pipeline for app instrumentation)

Deploy Prometheus and Grafana via **kube-prometheus-stack** Helm chart,
which bundles node-exporter, kube-state-metrics, and Grafana with
pre-configured datasources. OTel Collector runs as a DaemonSet receiving
OTLP from applications and exporting to Prometheus via remote write.

## Alternatives Considered

| Tool | Reason for Rejection |
|------|---------------------|
| Datadog | Commercial, vendor lock-in, cost |
| ELK Stack | Heavier footprint, log-focused not metrics-first |
| CloudWatch | AWS-only, limited dashboard flexibility |
| Mimir/VictoriaMetrics | Solve scale problems we don't have in a demo |

## Consequences

- Multiple components to wire (Prometheus, Grafana, OTel, exporters)
- OTel Collector config requires manual verification of endpoints
- Prometheus remote write receiver must be explicitly enabled
- kube-prometheus-stack provides batteries-included setup (reduces config)
- Sample app uses OTel auto-instrumentation for zero-code traces/metrics
