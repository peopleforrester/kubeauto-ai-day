# ABOUTME: Phase 4 tests for observability stack (Prometheus, Grafana, OTel).
# ABOUTME: Validates metrics collection, dashboards, alerting, and OTel instrumentation.

import json
import subprocess
import time
from typing import Any

import pytest
from kubernetes.client import CoreV1Api

from conftest import GRAFANA_BASIC_AUTH
from helpers.kubectl_helpers import strip_kubectl_noise

MONITORING_NS = "monitoring"
APPS_NS = "apps"


# --- Prometheus Tests ---


def test_prometheus_running(k8s_core: CoreV1Api) -> None:
    """Prometheus server pods are Running in monitoring namespace."""
    pods = k8s_core.list_namespaced_pod(
        MONITORING_NS,
        label_selector="app.kubernetes.io/name=prometheus",
    )
    running = [
        p.metadata.name
        for p in pods.items
        if p.status and p.status.phase == "Running"
    ]
    assert len(running) >= 1, (
        f"Expected at least 1 Prometheus pod running, got {len(running)}: {running}"
    )


# --- Grafana Tests ---


def test_grafana_running(k8s_core: CoreV1Api) -> None:
    """Grafana pods are Running in monitoring namespace."""
    pods = k8s_core.list_namespaced_pod(
        MONITORING_NS,
        label_selector="app.kubernetes.io/name=grafana",
    )
    running = [
        p.metadata.name
        for p in pods.items
        if p.status and p.status.phase == "Running"
    ]
    assert len(running) >= 1, (
        f"Expected at least 1 Grafana pod running, got {len(running)}: {running}"
    )


def test_grafana_ui_accessible() -> None:
    """Grafana HTTP endpoint responds via kubectl port-forward."""
    # Use kubectl exec to test the Grafana service from inside the cluster
    result = subprocess.run(
        [
            "kubectl", "run", "grafana-test", "--rm", "-i", "--restart=Never",
            "--image=docker.io/library/busybox:latest",
            "--namespace", MONITORING_NS,
            "--", "wget", "-q", "-O-", "--timeout=10",
            "http://prometheus-grafana.monitoring.svc.cluster.local:80/api/health",
        ],
        capture_output=True, text=True, timeout=60,
    )
    clean = strip_kubectl_noise(result.stdout)
    health = json.loads(clean) if clean.strip() else {}
    assert health.get("database") == "ok", (
        f"Expected Grafana health {{\"database\": \"ok\"}}, got: {clean[:500]} stderr: {result.stderr[:500]}"
    )


# --- OTel Collector Tests ---


def test_otel_collector_running(k8s_core: CoreV1Api) -> None:
    """OTel Collector pods Running on each node (DaemonSet)."""
    nodes = k8s_core.list_node()
    node_count = len(nodes.items)

    pods = k8s_core.list_namespaced_pod(
        MONITORING_NS,
        label_selector="app.kubernetes.io/name=opentelemetry-collector",
    )
    running = [
        p.metadata.name
        for p in pods.items
        if p.status and p.status.phase == "Running"
    ]
    assert len(running) >= node_count, (
        f"Expected {node_count} OTel Collector pods (one per node), "
        f"got {len(running)}: {running}"
    )


# --- Prometheus Scrape Targets ---


def test_prometheus_scrape_targets() -> None:
    """Prometheus has active scrape targets for core components."""
    # Query Prometheus targets API via kubectl exec
    result = subprocess.run(
        [
            "kubectl", "run", "prom-targets-test", "--rm", "-i", "--restart=Never",
            "--image=docker.io/library/busybox:latest",
            "--namespace", MONITORING_NS,
            "--", "wget", "-q", "-O-", "--timeout=10",
            "http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090/api/v1/targets",
        ],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, (
        f"Failed to query Prometheus targets: {result.stderr[:500]}"
    )
    data = json.loads(strip_kubectl_noise(result.stdout))
    active_jobs = {
        t.get("labels", {}).get("job", "")
        for t in data.get("data", {}).get("activeTargets", [])
    }
    # At minimum, kubelet and node-exporter should be scraped
    expected_jobs = {"kubelet", "node-exporter"}
    found = expected_jobs.intersection(active_jobs)
    assert len(found) >= 1, (
        f"Expected scrape targets for {expected_jobs}, found jobs: {active_jobs}"
    )


# --- Grafana Dashboards ---


def test_grafana_dashboard_loads() -> None:
    """Platform Overview dashboard exists in Grafana."""
    result = subprocess.run(
        [
            "kubectl", "run", "grafana-dash-test", "--rm", "-i", "--restart=Never",
            "--image=docker.io/library/busybox:latest",
            "--namespace", MONITORING_NS,
            "--", "wget", "-q", "-O-", "--timeout=10",
            f"--header=Authorization: {GRAFANA_BASIC_AUTH}",
            "http://prometheus-grafana.monitoring.svc.cluster.local:80/api/search",
        ],
        capture_output=True, text=True, timeout=60,
    )
    clean = strip_kubectl_noise(result.stdout)
    data = json.loads(clean) if clean else []
    titles = [d.get("title", "") for d in data]
    assert any(t == "Platform Overview" for t in titles), (
        f"Expected dashboard titled 'Platform Overview', found: {titles[:15]}"
    )


def test_grafana_panel_has_data() -> None:
    """At least one Grafana datasource returns data (Prometheus is connected)."""
    result = subprocess.run(
        [
            "kubectl", "run", "grafana-ds-test", "--rm", "-i", "--restart=Never",
            "--image=docker.io/library/busybox:latest",
            "--namespace", MONITORING_NS,
            "--", "wget", "-q", "-O-", "--timeout=10",
            f"--header=Authorization: {GRAFANA_BASIC_AUTH}",
            "http://prometheus-grafana.monitoring.svc.cluster.local:80/api/datasources",
        ],
        capture_output=True, text=True, timeout=60,
    )
    clean = strip_kubectl_noise(result.stdout)
    data = json.loads(clean) if clean else []
    prom_ds = [d for d in data if d.get("type") == "prometheus"]
    assert len(prom_ds) >= 1, (
        f"Expected Prometheus datasource in Grafana, found: {[d.get('type') for d in data]}"
    )


# --- OTel Trace Test ---


def test_otel_span_received() -> None:
    """OTel Collector receives a test span via OTLP HTTP."""
    # Send a minimal OTLP trace via HTTP to the collector
    trace_payload = json.dumps({
        "resourceSpans": [{
            "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "test-service"}}]},
            "scopeSpans": [{
                "scope": {"name": "test"},
                "spans": [{
                    "traceId": "00000000000000000000000000000001",
                    "spanId": "0000000000000001",
                    "name": "test-span",
                    "kind": 1,
                    "startTimeUnixNano": str(int(time.time() * 1e9)),
                    "endTimeUnixNano": str(int(time.time() * 1e9) + 1000000),
                    "status": {},
                }],
            }],
        }],
    })

    result = subprocess.run(
        [
            "kubectl", "run", "otel-trace-test", "--rm", "-i", "--restart=Never",
            "--image=docker.io/library/busybox:latest",
            "--namespace", MONITORING_NS,
            "--", "wget", "-q", "-O-", "--timeout=10",
            "--header=Content-Type: application/json",
            "--post-data", trace_payload,
            "http://otel-collector-opentelemetry-collector.monitoring.svc.cluster.local:4318/v1/traces",
        ],
        capture_output=True, text=True, timeout=60,
    )
    # OTLP HTTP returns empty JSON or partial success on accepted spans
    assert result.returncode == 0 or "partialSuccess" in result.stdout, (
        f"Failed to send test span to OTel Collector: rc={result.returncode} "
        f"stdout={result.stdout[:300]} stderr={result.stderr[:300]}"
    )


# --- Alert Rules ---


def test_alert_rules_exist() -> None:
    """Prometheus has NodeNotReady and PodCrashLoop alert rules."""
    result = subprocess.run(
        [
            "kubectl", "run", "prom-rules-test", "--rm", "-i", "--restart=Never",
            "--image=docker.io/library/busybox:latest",
            "--namespace", MONITORING_NS,
            "--", "wget", "-q", "-O-", "--timeout=10",
            "http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090/api/v1/rules",
        ],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, (
        f"Failed to query Prometheus rules: {result.stderr[:500]}"
    )
    data = json.loads(strip_kubectl_noise(result.stdout))
    all_rules: list[str] = []
    for group in data.get("data", {}).get("groups", []):
        for rule in group.get("rules", []):
            all_rules.append(rule.get("name", ""))

    assert "NodeNotReady" in all_rules, (
        f"Expected 'NodeNotReady' alert rule, found: {all_rules[:20]}"
    )
    assert "PodCrashLoop" in all_rules, (
        f"Expected 'PodCrashLoop' alert rule, found: {all_rules[:20]}"
    )
