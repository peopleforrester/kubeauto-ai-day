# Phase 4: Observability (Budget: 90 min)

**Goal:** Full observability stack with metrics, traces flowing through OTel Collector to Prometheus and Grafana.

**Inputs:** Secured cluster from Phase 3.

**Outputs:**
- Prometheus (kube-prometheus-stack) installed via ArgoCD, includes Grafana 12.x
- OTel Collector 0.140+ deployed as DaemonSet (OTLP receivers, Prometheus remote write export)
- Grafana dashboards: platform overview, ArgoCD sync, Kyverno policy, Falco alerts
- Alert rules: NodeNotReady, PodCrashLoop, ArgoCDAppDegraded, FalcoCriticalAlert
- Sample Python Flask app with OTel auto-instrumentation in `apps` namespace

**Test Criteria (tests/test_phase_04_observability.py):**
- Prometheus pods Running
- Grafana pods Running, UI accessible
- OTel Collector pods Running on each node
- Prometheus scrape targets include kubelet, node-exporter, kube-state-metrics, ArgoCD, Kyverno
- Grafana: platform-overview dashboard loads
- Grafana: at least one panel shows non-zero data
- OTel: test span appears in backend
- Alert rules exist for NodeNotReady, PodCrashLoop

**Completion Promise:** `<promise>PHASE4_DONE</promise>`

**Known Risk:** OTel Collector config generates plausible YAML that doesn't work. Manual review mandatory.

**ADR:** ADR-005 (Observability: OTel + Prometheus + Grafana)
**Commits:** 4 (Prometheus+Grafana; OTel Collector; Dashboards+alerts; Sample app)
