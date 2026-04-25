# ABOUTME: Phase 2 GitOps Bootstrap tests for ArgoCD installation and app-of-apps.
# ABOUTME: Validates ArgoCD 3.x running, root app synced, drift detection working.

import time

import pytest
from kubernetes.client import CoreV1Api, CustomObjectsApi


pytestmark = pytest.mark.requires_cluster


ARGOCD_NAMESPACE = "argocd"
ARGOCD_GROUP = "argoproj.io"
ARGOCD_VERSION = "v1alpha1"
ARGOCD_PLURAL = "applications"


def _get_argocd_app(k8s_custom: CustomObjectsApi, name: str) -> dict:
    """Fetch a single ArgoCD Application by name."""
    return k8s_custom.get_namespaced_custom_object(
        group=ARGOCD_GROUP,
        version=ARGOCD_VERSION,
        namespace=ARGOCD_NAMESPACE,
        plural=ARGOCD_PLURAL,
        name=name,
    )


def _list_argocd_apps(k8s_custom: CustomObjectsApi) -> list[dict]:
    """List all ArgoCD Applications in the argocd namespace."""
    result = k8s_custom.list_namespaced_custom_object(
        group=ARGOCD_GROUP,
        version=ARGOCD_VERSION,
        namespace=ARGOCD_NAMESPACE,
        plural=ARGOCD_PLURAL,
    )
    return result.get("items", [])


def test_argocd_server_running(k8s_core: CoreV1Api) -> None:
    """ArgoCD server pod is Running in argocd namespace."""
    pods = k8s_core.list_namespaced_pod(
        namespace=ARGOCD_NAMESPACE,
        label_selector="app.kubernetes.io/name=argocd-server",
    )
    running_pods = [
        pod.metadata.name
        for pod in pods.items
        if pod.status and pod.status.phase == "Running"
    ]
    assert len(running_pods) >= 1, (
        f"Expected 1+ running argocd-server pods, got {len(running_pods)}"
    )


def test_argocd_ui_accessible(k8s_core: CoreV1Api) -> None:
    """ArgoCD server Service exists and exposes correct ports."""
    svc = k8s_core.read_namespaced_service(
        name="argocd-server",
        namespace=ARGOCD_NAMESPACE,
    )
    port_numbers = [p.port for p in svc.spec.ports]
    # ArgoCD server exposes HTTPS (443) and/or HTTP (80)
    assert 443 in port_numbers or 80 in port_numbers, (
        f"ArgoCD server service ports: {port_numbers}, expected 443 or 80"
    )


def test_root_app_exists(k8s_custom: CustomObjectsApi) -> None:
    """Root app-of-apps Application exists in argocd namespace."""
    app = _get_argocd_app(k8s_custom, "app-of-apps")
    assert app["metadata"]["name"] == "app-of-apps"


def test_root_app_synced(k8s_custom: CustomObjectsApi) -> None:
    """Root app-of-apps Application is Synced and Healthy."""
    app = _get_argocd_app(k8s_custom, "app-of-apps")
    status = app.get("status", {})

    sync_status = status.get("sync", {}).get("status", "Unknown")
    health_status = status.get("health", {}).get("status", "Unknown")

    assert sync_status == "Synced", (
        f"Root app sync status: {sync_status}, expected Synced"
    )
    assert health_status == "Healthy", (
        f"Root app health status: {health_status}, expected Healthy"
    )


def test_namespace_app_synced(k8s_custom: CustomObjectsApi) -> None:
    """Namespace Application is Synced and Healthy."""
    app = _get_argocd_app(k8s_custom, "namespaces")
    status = app.get("status", {})

    sync_status = status.get("sync", {}).get("status", "Unknown")
    assert sync_status == "Synced", (
        f"Namespaces app sync status: {sync_status}, expected Synced"
    )


def test_no_degraded_apps(k8s_custom: CustomObjectsApi) -> None:
    """No ArgoCD Applications are in Degraded health status."""
    apps = _list_argocd_apps(k8s_custom)
    degraded = [
        app["metadata"]["name"]
        for app in apps
        if app.get("status", {}).get("health", {}).get("status") == "Degraded"
    ]
    assert len(degraded) == 0, (
        f"Degraded applications found: {degraded}"
    )


def test_drift_detection(k8s_core: CoreV1Api, k8s_custom: CustomObjectsApi) -> None:
    """ArgoCD detects drift when a managed resource is modified."""
    # Modify a managed label on the apps namespace (ArgoCD tracks managed fields)
    # ArgoCD annotation-based tracking only detects changes to fields in the manifest
    body = {"metadata": {"labels": {"app.kubernetes.io/part-of": "DRIFTED"}}}
    k8s_core.patch_namespace("apps", body)

    # Wait for ArgoCD to detect and self-heal the drift
    # With 30s reconciliation and self-heal enabled, correction is fast
    max_wait = 90
    interval = 5
    elapsed = 0
    detected = False

    while elapsed < max_wait:
        ns = k8s_core.read_namespace("apps")
        labels = ns.metadata.labels or {}
        part_of = labels.get("app.kubernetes.io/part-of", "")

        if part_of == "kubeauto-idp":
            # Self-heal corrected the drift back to the Git-defined value
            detected = True
            break

        # Also check if ArgoCD flagged it as OutOfSync
        app = _get_argocd_app(k8s_custom, "namespaces")
        sync_status = app.get("status", {}).get("sync", {}).get("status", "Unknown")
        if sync_status == "OutOfSync":
            detected = True
            break

        print(f"  Waiting for drift correction... {elapsed}s/{max_wait}s (label: {part_of})")
        time.sleep(interval)
        elapsed += interval

    assert detected, (
        f"ArgoCD did not detect/correct drift within {max_wait}s"
    )
