# Phase 4: Observability — Prompt Log

## Summary

- **Start time:** 2026-02-17 ~19:00 EST
- **End time:** 2026-02-17 ~19:35 EST
- **Total AI time:** 28 min (Prom+Grafana 8 + OTel 15 + Dashboards 3 + Alerts 2)
- **Correction prompts:** 4 (OTel 3, Prom 1)
- **Components:** Prometheus + Grafana, OTel Collector Config, Grafana Dashboards, Alert Rules

*Note: Prompts reconstructed from git history, scorecard notes, and session data.*

---

## Prompt 1 (Phase 4, ~19:00)
**Type:** Initial
**Prompt:** Write Phase 4 tests, then deploy kube-prometheus-stack 82.1.0 with Grafana, remote write receiver, and custom alert rules.
**Result:** Partial — deployed cleanly but test had stdout noise issue
**Time spent:** 8 min
**Correction needed:** Yes — kubectl run stdout noise (pod deletion message) broke JSON parsing in test
**Notes:** Chart 82.1.0 includes Prometheus 3.9.1 and Grafana 12.3.3. Remote write receiver needed for OTel Collector.

## Prompt 2 (Phase 4, ~19:08)
**Type:** Initial
**Prompt:** Deploy OTel Collector as DaemonSet with OTLP receivers and prometheusremotewrite exporter.
**Result:** Failure — 3 correction cycles
**Time spent:** 15 min
**Correction needed:** Yes

## Prompt 3 (Phase 4, ~19:12)
**Type:** Correction
**Prompt:** OTel Collector pods in CrashLoopBackOff — prometheusremotewrite exporter not found.
**Result:** Partial — changed to contrib image but service still missing
**Time spent:** 5 min
**Correction needed:** Yes — k8s image lacks exporters, needed contrib

## Prompt 4 (Phase 4, ~19:17)
**Type:** Correction
**Prompt:** OTel Collector service not reachable — apps can't send OTLP telemetry.
**Result:** Success — DaemonSet mode doesn't create ClusterIP service by default
**Time spent:** 3 min
**Correction needed:** Set `service.enabled: true` explicitly

## Prompt 5 (Phase 4, ~19:20)
**Type:** Initial
**Prompt:** Create Platform Overview Grafana dashboard with 8 panels and 4 custom PrometheusRules.
**Result:** Success — both correct first try
**Time spent:** 5 min total
**Correction needed:** No
**Notes:** ConfigMap sidecar provisioning for dashboards worked immediately. 4 alert rules (NodeNotReady, PodCrashLoop, ArgoCDAppDegraded, FalcoCriticalAlert) via additionalPrometheusRulesMap.

## Test Results
- 36 tests passing after Phase 4
- Commits: `060d2f5` through `7ec0aed` (5 commits)
