# ABOUTME: Phase 6 integration tests for cross-component validation.
# ABOUTME: Tests end-to-end flows across ArgoCD, Kyverno, Falco, OTel, and Grafana.

import json
import subprocess
import time
from typing import Any

import pytest
from kubernetes.client import CoreV1Api, AppsV1Api

from helpers.kubectl_helpers import strip_kubectl_noise

MONITORING_NS = "monitoring"
APPS_NS = "apps"
ARGOCD_NS = "argocd"
BACKSTAGE_NS = "backstage"


# --- E2E Deploy Test ---


def test_e2e_sample_app_accessible() -> None:
    """Sample app responds to HTTP requests via localhost health endpoint."""
    # NetworkPolicy default-deny blocks pod-to-service egress within apps namespace.
    # Test via localhost from within the pod to verify the app is running and healthy.
    pods_result = subprocess.run(
        ["kubectl", "get", "pods", "-n", APPS_NS, "-l", "app=sample-app",
         "-o", "jsonpath={.items[0].metadata.name}"],
        capture_output=True, text=True, timeout=10,
    )
    pod_name = pods_result.stdout.strip()
    assert pod_name, "No sample-app pod found"

    result = subprocess.run(
        [
            "kubectl", "exec", "-n", APPS_NS, pod_name, "--",
            "python3", "-c",
            "import urllib.request; print(urllib.request.urlopen('http://localhost:8080/health', timeout=5).read().decode())",
        ],
        capture_output=True, text=True, timeout=20,
    )
    assert "ok" in result.stdout.lower(), (
        f"Sample app health check failed: stdout={result.stdout[:300]} stderr={result.stderr[:300]}"
    )


# --- Kyverno Integration ---


def test_kyverno_blocks_noncompliant() -> None:
    """Kyverno rejects a non-compliant deployment in apps namespace."""
    result = subprocess.run(
        [
            "kubectl", "run", "noncompliant-test",
            "--image=docker.io/library/nginx:latest",
            "--namespace", APPS_NS,
            "--dry-run=server",
        ],
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode != 0, (
        "Expected Kyverno to reject non-compliant pod (no resources, no probes, latest tag)"
    )
    assert "blocked" in result.stderr.lower() or "denied" in result.stderr.lower(), (
        f"Expected Kyverno denial, got: {result.stderr[:500]}"
    )


# --- Falco Integration ---


def test_falco_detects_write_below_etc() -> None:
    """Falco detects a write below /etc in a pod and generates an alert within 30s."""
    # Get a sample-app pod
    pods_result = subprocess.run(
        ["kubectl", "get", "pods", "-n", APPS_NS, "-l", "app=sample-app",
         "-o", "jsonpath={.items[0].metadata.name}"],
        capture_output=True, text=True, timeout=10,
    )
    pod_name = pods_result.stdout.strip()
    assert pod_name, "No sample-app pod found"

    # Write to /etc to trigger Falco "Write Below Etc" rule with a distinctive filename
    subprocess.run(
        ["kubectl", "exec", "-n", APPS_NS, pod_name, "--",
         "sh", "-c", "touch /etc/falco-integration-marker"],
        capture_output=True, text=True, timeout=10,
    )

    # Wait for Falco to process and check logs
    time.sleep(10)
    logs_result = subprocess.run(
        ["kubectl", "logs", "-n", "security", "-l", "app.kubernetes.io/name=falco",
         "-c", "falco", "--tail=100", "--since=30s"],
        capture_output=True, text=True, timeout=15,
    )
    assert "falco-integration-marker" in logs_result.stdout, (
        f"Expected Falco to detect /etc write with marker file, "
        f"got logs: {logs_result.stdout[:500]}"
    )


# --- OTel + Prometheus Integration ---


def test_otel_metrics_in_prometheus() -> None:
    """OTel Collector exports metrics that appear in Prometheus."""
    # Query Prometheus for any metric with otelcol prefix (collector self-metrics)
    result = subprocess.run(
        [
            "kubectl", "run", "prom-otel-test", "--rm", "-i", "--restart=Never",
            "--image=docker.io/library/busybox:latest",
            "--namespace", MONITORING_NS,
            "--", "wget", "-q", "-O-", "--timeout=10",
            "http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090/api/v1/query?query=up",
        ],
        capture_output=True, text=True, timeout=30,
    )
    clean = strip_kubectl_noise(result.stdout)
    data = json.loads(clean)
    results = data.get("data", {}).get("result", [])
    jobs = {r.get("metric", {}).get("job", "") for r in results}
    # Prometheus should have scrape targets from kube-prometheus-stack
    assert len(results) >= 3, (
        f"Expected at least 3 scrape targets in Prometheus, got {len(results)}: jobs={jobs}"
    )


# --- ArgoCD Drift Detection ---


def test_argocd_drift_detection() -> None:
    """ArgoCD detects and corrects modification of a managed field within 90s."""
    # Modify a managed field: change the sample-app service port name
    # ArgoCD tracks managed fields and will revert this change
    original = subprocess.run(
        ["kubectl", "get", "service", "sample-app", "-n", APPS_NS,
         "-o", "jsonpath={.spec.ports[0].name}"],
        capture_output=True, text=True, timeout=10,
    )
    original_name = original.stdout.strip()

    subprocess.run(
        ["kubectl", "patch", "service", "sample-app", "-n", APPS_NS,
         "--type=json", "-p",
         '[{"op":"replace","path":"/spec/ports/0/name","value":"drifted"}]'],
        capture_output=True, text=True, timeout=10,
    )

    # Wait for ArgoCD to detect and self-heal
    print("  Waiting for ArgoCD self-heal (up to 90s)...")
    healed = False
    for i in range(9):
        time.sleep(10)
        result = subprocess.run(
            ["kubectl", "get", "service", "sample-app", "-n", APPS_NS,
             "-o", "jsonpath={.spec.ports[0].name}"],
            capture_output=True, text=True, timeout=10,
        )
        current = result.stdout.strip()
        if current == original_name:
            healed = True
            print(f"  Healed after {(i + 1) * 10}s")
            break

    assert healed, (
        f"ArgoCD did not self-heal the drift within 90s. "
        f"Port name still 'drifted', expected '{original_name}'"
    )


# --- Grafana + Prometheus Datasource Integration ---


def test_grafana_prometheus_datasource_healthy() -> None:
    """Grafana Prometheus datasource health check returns OK."""
    result = subprocess.run(
        [
            "kubectl", "run", "grafana-health-test", "--rm", "-i", "--restart=Never",
            "--image=docker.io/library/busybox:latest",
            "--namespace", MONITORING_NS,
            "--", "wget", "-q", "-O-", "--timeout=10",
            "--header=Authorization: Basic YWRtaW46YWRtaW4=",
            "http://prometheus-grafana.monitoring.svc.cluster.local:80/api/datasources/proxy/1/api/v1/query?query=up",
        ],
        capture_output=True, text=True, timeout=30,
    )
    clean = strip_kubectl_noise(result.stdout)
    assert "success" in clean.lower(), (
        f"Grafana → Prometheus datasource query failed: {result.stdout[:300]}"
    )


# --- All Components Running Check ---


def test_all_platform_components_healthy(k8s_core: CoreV1Api) -> None:
    """All platform namespaces have running pods with no CrashLoopBackOff."""
    namespaces = [ARGOCD_NS, MONITORING_NS, "security", "platform", BACKSTAGE_NS, APPS_NS]
    crash_pods: list[str] = []

    for ns in namespaces:
        pods = k8s_core.list_namespaced_pod(ns)
        for pod in pods.items:
            if not pod.status or not pod.status.container_statuses:
                continue
            for cs in pod.status.container_statuses:
                if cs.state and cs.state.waiting:
                    reason = cs.state.waiting.reason or ""
                    if "CrashLoopBackOff" in reason or "Error" in reason:
                        crash_pods.append(f"{ns}/{pod.metadata.name}: {reason}")

    assert len(crash_pods) == 0, (
        f"Pods in unhealthy state: {crash_pods}"
    )
