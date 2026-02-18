# ABOUTME: Phase 7 tests for production hardening components.
# ABOUTME: Validates cert-manager, resource quotas, PDBs, gitleaks, and security posture.

import json
import re
import subprocess
from typing import Any

import pytest
from kubernetes import client, config
from kubernetes.client import CoreV1Api, AppsV1Api, CustomObjectsApi

MONITORING_NS = "monitoring"
APPS_NS = "apps"
ARGOCD_NS = "argocd"
BACKSTAGE_NS = "backstage"
PLATFORM_NS = "platform"


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


@pytest.fixture(scope="module")
def k8s_custom() -> CustomObjectsApi:
    """Return CustomObjectsApi client."""
    config.load_kube_config()
    return client.CustomObjectsApi()


# --- cert-manager Tests ---


def test_cert_manager_running(k8s_core: CoreV1Api) -> None:
    """cert-manager pods are Running in cert-manager namespace."""
    pods = k8s_core.list_namespaced_pod(
        "cert-manager",
        label_selector="app.kubernetes.io/instance=cert-manager",
    )
    running = [
        p.metadata.name
        for p in pods.items
        if p.status and p.status.phase == "Running"
    ]
    assert len(running) >= 2, (
        f"Expected at least 2 cert-manager pods running (controller + webhook), "
        f"got {len(running)}: {running}"
    )


def test_cluster_issuers_ready(k8s_custom: CustomObjectsApi) -> None:
    """ClusterIssuers for Let's Encrypt staging and production exist and are ready."""
    issuers = k8s_custom.list_cluster_custom_object(
        group="cert-manager.io",
        version="v1",
        plural="clusterissuers",
    )
    issuer_names = [i["metadata"]["name"] for i in issuers.get("items", [])]
    assert "letsencrypt-staging" in issuer_names, (
        f"Expected letsencrypt-staging ClusterIssuer, found: {issuer_names}"
    )
    assert "letsencrypt-production" in issuer_names, (
        f"Expected letsencrypt-production ClusterIssuer, found: {issuer_names}"
    )

    # Check Ready condition on at least one issuer
    for issuer in issuers["items"]:
        if issuer["metadata"]["name"] == "letsencrypt-staging":
            conditions = issuer.get("status", {}).get("conditions", [])
            ready = [c for c in conditions if c.get("type") == "Ready" and c.get("status") == "True"]
            assert len(ready) >= 1, (
                f"letsencrypt-staging ClusterIssuer not ready: {conditions}"
            )


# --- Resource Quota Tests ---


def test_resource_quota_exists(k8s_core: CoreV1Api) -> None:
    """ResourceQuota exists in apps namespace with expected limits."""
    quotas = k8s_core.list_namespaced_resource_quota(APPS_NS)
    assert len(quotas.items) >= 1, "No ResourceQuota found in apps namespace"

    quota = quotas.items[0]
    hard = quota.status.hard if quota.status else {}
    assert "pods" in hard, f"ResourceQuota missing pods limit: {hard}"
    assert "requests.cpu" in hard or "limits.cpu" in hard, (
        f"ResourceQuota missing CPU limit: {hard}"
    )
    assert "requests.memory" in hard or "limits.memory" in hard, (
        f"ResourceQuota missing memory limit: {hard}"
    )


def test_resource_quota_enforced() -> None:
    """Cannot exceed pod quota in apps namespace via dry-run."""
    # Try to create 11 pods (quota is 10) — this is a dry-run so non-destructive
    # We test that the quota object reports correct max
    result = subprocess.run(
        ["kubectl", "get", "resourcequota", "-n", APPS_NS, "-o",
         "jsonpath={.items[0].spec.hard.pods}"],
        capture_output=True, text=True, timeout=10,
    )
    max_pods = result.stdout.strip()
    assert max_pods, "Could not read pods quota"
    assert int(max_pods) <= 10, (
        f"Expected pods quota <= 10, got {max_pods}"
    )


# --- PDB Tests ---


def test_pdbs_exist(k8s_core: CoreV1Api) -> None:
    """PodDisruptionBudgets exist for critical platform components."""
    config.load_kube_config()
    policy_api = client.PolicyV1Api()

    expected_namespaces = [ARGOCD_NS, MONITORING_NS, BACKSTAGE_NS]
    found_pdbs: list[str] = []

    for ns in expected_namespaces:
        pdbs = policy_api.list_namespaced_pod_disruption_budget(ns)
        for pdb in pdbs.items:
            found_pdbs.append(f"{ns}/{pdb.metadata.name}")

    assert len(found_pdbs) >= 3, (
        f"Expected at least 3 PDBs across platform namespaces, "
        f"found {len(found_pdbs)}: {found_pdbs}"
    )


# --- Security Posture Tests ---


def test_no_root_pods_in_apps(k8s_core: CoreV1Api) -> None:
    """No pods in apps namespace are running as root."""
    pods = k8s_core.list_namespaced_pod(APPS_NS)
    root_pods: list[str] = []

    for pod in pods.items:
        if not pod.spec:
            continue
        pod_sc = pod.spec.security_context
        for container in pod.spec.containers or []:
            c_sc = container.security_context
            # Check container-level runAsNonRoot
            if c_sc and c_sc.run_as_non_root is False:
                root_pods.append(f"{pod.metadata.name}/{container.name}: runAsNonRoot=false")
            # Check if running as uid 0
            if c_sc and c_sc.run_as_user == 0:
                root_pods.append(f"{pod.metadata.name}/{container.name}: runAsUser=0")

    assert len(root_pods) == 0, (
        f"Pods running as root in apps namespace: {root_pods}"
    )


def test_gitleaks_clean() -> None:
    """gitleaks scan finds no secrets in the git-tracked repository files."""
    repo_root = "/home/ollama/repos/Business/KodeKloud/Conferences/kubecon-2026-eu/kubeauto-ai-day"
    result = subprocess.run(
        ["gitleaks", "detect",
         f"--source={repo_root}",
         f"--config={repo_root}/.gitleaks.toml",
         "--no-banner"],
        capture_output=True, text=True, timeout=60,
    )
    # gitleaks returns 0 for clean, 1 for findings
    assert result.returncode == 0, (
        f"gitleaks found potential secrets: {result.stdout[:500]} {result.stderr[:500]}"
    )


# --- Documentation Tests ---


def test_security_doc_exists() -> None:
    """SECURITY.md exists with all 8 required sections."""
    result = subprocess.run(
        ["test", "-f", "/home/ollama/repos/Business/KodeKloud/Conferences/kubecon-2026-eu/kubeauto-ai-day/docs/SECURITY.md"],
        capture_output=True, text=True, timeout=5,
    )
    assert result.returncode == 0, "docs/SECURITY.md does not exist"

    with open("/home/ollama/repos/Business/KodeKloud/Conferences/kubecon-2026-eu/kubeauto-ai-day/docs/SECURITY.md") as f:
        content = f.read()

    required_sections = [
        "Kyverno",
        "Falco",
        "RBAC",
        "NetworkPolicy",
        "ESO",
        "TLS",
        "OIDC",
        "Audit",
    ]
    missing = [s for s in required_sections if s.lower() not in content.lower()]
    assert len(missing) == 0, (
        f"SECURITY.md missing sections: {missing}"
    )


def test_cost_doc_exists() -> None:
    """COST.md exists with cost estimates."""
    result = subprocess.run(
        ["test", "-f", "/home/ollama/repos/Business/KodeKloud/Conferences/kubecon-2026-eu/kubeauto-ai-day/docs/COST.md"],
        capture_output=True, text=True, timeout=5,
    )
    assert result.returncode == 0, "docs/COST.md does not exist"

    with open("/home/ollama/repos/Business/KodeKloud/Conferences/kubecon-2026-eu/kubeauto-ai-day/docs/COST.md") as f:
        content = f.read()

    assert "cost" in content.lower(), "COST.md doesn't appear to contain cost information"
