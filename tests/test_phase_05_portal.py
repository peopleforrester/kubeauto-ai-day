# ABOUTME: Phase 5 tests for Backstage developer portal.
# ABOUTME: Validates catalog, templates, and service deployment via template skeleton.

import json
import re
import subprocess
from typing import Any

import pytest
from kubernetes import client, config
from kubernetes.client import CoreV1Api, AppsV1Api, CustomObjectsApi

BACKSTAGE_NS = "backstage"
APPS_NS = "apps"


def _strip_kubectl_noise(stdout: str) -> str:
    """Remove trailing 'pod \"xxx\" deleted' line from kubectl run --rm output."""
    return re.sub(r'pod "[\w-]+" deleted\s*$', "", stdout).strip()


@pytest.fixture(scope="module")
def k8s_core() -> CoreV1Api:
    """Load kubeconfig and return CoreV1Api client."""
    config.load_kube_config()
    return client.CoreV1Api()


@pytest.fixture(scope="module")
def k8s_apps() -> AppsV1Api:
    """Return AppsV1Api client."""
    config.load_kube_config()
    return client.AppsV1Api()


# --- Backstage Pod Tests ---


def test_backstage_running(k8s_core: CoreV1Api) -> None:
    """Backstage pod is Running in backstage namespace."""
    pods = k8s_core.list_namespaced_pod(
        BACKSTAGE_NS,
        label_selector="app.kubernetes.io/name=backstage",
    )
    running = [
        p.metadata.name
        for p in pods.items
        if p.status and p.status.phase == "Running"
    ]
    assert len(running) >= 1, (
        f"Expected at least 1 Backstage pod running, got {len(running)}: {running}"
    )


def test_backstage_ui_accessible() -> None:
    """Backstage HTTP endpoint responds with 200."""
    result = subprocess.run(
        [
            "kubectl", "run", "backstage-health-test", "--rm", "-i",
            "--restart=Never",
            "--image=docker.io/library/busybox:latest",
            "--namespace", BACKSTAGE_NS,
            "--", "wget", "-q", "-O-", "--timeout=10",
            "http://backstage.backstage.svc.cluster.local:7007/api/catalog/entities?limit=1",
        ],
        capture_output=True, text=True, timeout=30,
    )
    clean = _strip_kubectl_noise(result.stdout)
    assert result.returncode == 0 or len(clean) > 0, (
        f"Backstage not responding: rc={result.returncode} "
        f"stdout={result.stdout[:300]} stderr={result.stderr[:300]}"
    )


# --- Catalog Tests ---


def test_catalog_has_component() -> None:
    """At least one Component entity exists in the Backstage catalog."""
    result = subprocess.run(
        [
            "kubectl", "run", "backstage-catalog-test", "--rm", "-i",
            "--restart=Never",
            "--image=docker.io/library/busybox:latest",
            "--namespace", BACKSTAGE_NS,
            "--", "wget", "-q", "-O-", "--timeout=10",
            "http://backstage.backstage.svc.cluster.local:7007/api/catalog/entities?filter=kind=component",
        ],
        capture_output=True, text=True, timeout=30,
    )
    clean = _strip_kubectl_noise(result.stdout)
    data = json.loads(clean) if clean else []
    components = [e.get("metadata", {}).get("name", "") for e in data]
    assert len(components) >= 1, (
        f"Expected at least 1 Component in catalog, got: {components}"
    )


def test_template_exists() -> None:
    """Deploy-service template exists in the Backstage catalog."""
    result = subprocess.run(
        [
            "kubectl", "run", "backstage-template-test", "--rm", "-i",
            "--restart=Never",
            "--image=docker.io/library/busybox:latest",
            "--namespace", BACKSTAGE_NS,
            "--", "wget", "-q", "-O-", "--timeout=10",
            "http://backstage.backstage.svc.cluster.local:7007/api/catalog/entities?filter=kind=template",
        ],
        capture_output=True, text=True, timeout=30,
    )
    clean = _strip_kubectl_noise(result.stdout)
    data = json.loads(clean) if clean else []
    template_names = [e.get("metadata", {}).get("name", "") for e in data]
    assert "deploy-service" in template_names, (
        f"Expected 'deploy-service' template, found: {template_names}"
    )


# --- Template Skeleton Validation Tests ---
# These tests validate the template skeleton produces Kyverno-compliant
# resources by deploying a test service using the same patterns.


def test_template_skeleton_deploys(k8s_apps: AppsV1Api) -> None:
    """Template skeleton deployment exists and is available in apps namespace."""
    # The templated-test-svc deployment is created by the skeleton validation
    # ArgoCD Application (gitops/apps/templated-test-svc.yaml)
    deployments = k8s_apps.list_namespaced_deployment(
        APPS_NS,
        label_selector="app=templated-test-svc",
    )
    available = [
        d.metadata.name
        for d in deployments.items
        if d.status and d.status.available_replicas and d.status.available_replicas >= 1
    ]
    assert len(available) >= 1, (
        f"Expected templated-test-svc deployment available, got: "
        f"{[d.metadata.name for d in deployments.items]}"
    )


def test_templated_pod_running(k8s_core: CoreV1Api) -> None:
    """Pod from template skeleton is Running in apps namespace."""
    pods = k8s_core.list_namespaced_pod(
        APPS_NS,
        label_selector="app=templated-test-svc",
    )
    running = [
        p.metadata.name
        for p in pods.items
        if p.status and p.status.phase == "Running"
    ]
    assert len(running) >= 1, (
        f"Expected at least 1 templated-test-svc pod running, got {len(running)}"
    )


def test_templated_service_kyverno_compliant() -> None:
    """Template skeleton resources pass Kyverno policy dry-run validation."""
    # Attempt to create a pod matching the template skeleton pattern via dry-run
    result = subprocess.run(
        [
            "kubectl", "run", "kyverno-template-check",
            "--image=docker.io/library/nginx:1.27",
            "--namespace", APPS_NS,
            "--dry-run=server",
            "--overrides", json.dumps({
                "apiVersion": "v1",
                "spec": {
                    "securityContext": {
                        "runAsNonRoot": True,
                        "runAsUser": 1000,
                        "fsGroup": 1000,
                    },
                    "containers": [{
                        "name": "kyverno-template-check",
                        "image": "docker.io/library/nginx:1.27",
                        "ports": [{"containerPort": 8080}],
                        "resources": {
                            "requests": {"cpu": "100m", "memory": "128Mi"},
                            "limits": {"cpu": "500m", "memory": "256Mi"},
                        },
                        "readinessProbe": {
                            "httpGet": {"path": "/", "port": 8080},
                            "initialDelaySeconds": 5,
                        },
                        "livenessProbe": {
                            "httpGet": {"path": "/", "port": 8080},
                            "initialDelaySeconds": 10,
                        },
                        "securityContext": {
                            "allowPrivilegeEscalation": False,
                            "capabilities": {"drop": ["ALL"]},
                        },
                    }],
                },
                "metadata": {
                    "labels": {
                        "app": "kyverno-template-check",
                        "version": "v1.0.0",
                    },
                },
            }),
        ],
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, (
        f"Template skeleton pattern rejected by Kyverno: {result.stderr[:500]}"
    )
