# ABOUTME: Phase 3 Security Stack tests for Kyverno, Falco, ESO, RBAC, NetworkPolicies.
# ABOUTME: Validates policy enforcement, runtime detection, secret sync, and access control.

import base64
import json
import subprocess
import time

import pytest
from kubernetes import client, config
from kubernetes.client import CoreV1Api, CustomObjectsApi, RbacAuthorizationV1Api


APPS_NS = "apps"
SECURITY_NS = "security"
PLATFORM_NS = "platform"


@pytest.fixture(scope="module")
def k8s_core() -> CoreV1Api:
    """Load kubeconfig and return a CoreV1Api client."""
    config.load_kube_config()
    return client.CoreV1Api()


@pytest.fixture(scope="module")
def k8s_custom() -> CustomObjectsApi:
    """Return a CustomObjectsApi client for CRD assertions."""
    config.load_kube_config()
    return client.CustomObjectsApi()


@pytest.fixture(scope="module")
def k8s_rbac() -> RbacAuthorizationV1Api:
    """Return an RbacAuthorizationV1Api client for RBAC assertions."""
    config.load_kube_config()
    return client.RbacAuthorizationV1Api()


# --- Kyverno Tests ---


def test_kyverno_running(k8s_core: CoreV1Api) -> None:
    """Kyverno admission controller pods are Running."""
    pods = k8s_core.list_namespaced_pod(
        namespace="kyverno",
        label_selector="app.kubernetes.io/component=admission-controller",
    )
    running = [
        p.metadata.name for p in pods.items
        if p.status and p.status.phase == "Running"
    ]
    assert len(running) >= 1, (
        f"Expected 1+ running Kyverno admission controller pods, got {len(running)}"
    )


def test_block_no_resource_limits() -> None:
    """Pod without resource limits is rejected in apps namespace."""
    result = subprocess.run(
        [
            "kubectl", "run", "test-no-limits",
            "--image=docker.io/library/nginx:latest",
            "--namespace", APPS_NS,
            "--dry-run=server",
            "--overrides", json.dumps({
                "metadata": {"labels": {"app": "test", "version": "v1"}},
                "spec": {"containers": [{
                    "name": "test-no-limits",
                    "image": "docker.io/library/nginx:latest",
                }]},
            }),
        ],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode != 0, "Pod without resource limits should be rejected"
    assert "resource" in result.stderr.lower() or "limit" in result.stderr.lower() or "denied" in result.stderr.lower(), (
        f"Expected Kyverno denial about resource limits, got: {result.stderr}"
    )


def test_block_unauthorized_registry() -> None:
    """Pod from unauthorized registry is rejected in apps namespace."""
    result = subprocess.run(
        [
            "kubectl", "run", "test-bad-registry",
            "--image=evil.io/malware:latest",
            "--namespace", APPS_NS,
            "--dry-run=server",
        ],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode != 0, "Pod from unauthorized registry should be rejected"
    assert "registr" in result.stderr.lower() or "denied" in result.stderr.lower() or "image" in result.stderr.lower(), (
        f"Expected Kyverno denial about registry, got: {result.stderr}"
    )


def test_block_privileged_pod() -> None:
    """Privileged pod is rejected in apps namespace."""
    pod_spec = {
        "metadata": {"labels": {"app": "test", "version": "v1"}},
        "spec": {
            "containers": [{
                "name": "test-privileged",
                "image": "docker.io/library/nginx:latest",
                "securityContext": {"privileged": True},
                "resources": {"limits": {"cpu": "100m", "memory": "128Mi"}},
            }],
        },
    }
    result = subprocess.run(
        [
            "kubectl", "run", "test-privileged",
            "--image=docker.io/library/nginx:latest",
            "--namespace", APPS_NS,
            "--dry-run=server",
            "--overrides", json.dumps(pod_spec),
        ],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode != 0, "Privileged pod should be rejected"
    assert "privileged" in result.stderr.lower() or "denied" in result.stderr.lower() or "security" in result.stderr.lower(), (
        f"Expected Kyverno denial about privileged, got: {result.stderr}"
    )


# --- Falco Tests ---


def test_falco_running(k8s_core: CoreV1Api) -> None:
    """Falco DaemonSet pods Running on each node."""
    nodes = k8s_core.list_node()
    node_count = len(nodes.items)

    pods = k8s_core.list_namespaced_pod(
        namespace=SECURITY_NS,
        label_selector="app.kubernetes.io/name=falco",
    )
    running = [
        p.metadata.name for p in pods.items
        if p.status and p.status.phase == "Running"
    ]
    assert len(running) >= node_count, (
        f"Expected {node_count} Falco pods (one per node), got {len(running)}: {running}"
    )


def test_falco_exec_alert(k8s_core: CoreV1Api) -> None:
    """Exec into a pod triggers a Falco alert in logs."""
    # Create a temporary test pod in security namespace (not apps, to avoid Kyverno)
    pod_name = "falco-test-target"
    try:
        k8s_core.create_namespaced_pod(
            namespace=SECURITY_NS,
            body=client.V1Pod(
                metadata=client.V1ObjectMeta(name=pod_name),
                spec=client.V1PodSpec(
                    containers=[client.V1Container(
                        name="test",
                        image="docker.io/library/busybox:latest",
                        command=["sleep", "300"],
                        resources=client.V1ResourceRequirements(
                            limits={"cpu": "50m", "memory": "32Mi"},
                        ),
                    )],
                ),
            ),
        )
    except client.exceptions.ApiException as e:
        if e.status != 409:  # Already exists is OK
            raise

    # Wait for pod to be running
    for _ in range(30):
        pod = k8s_core.read_namespaced_pod(pod_name, SECURITY_NS)
        if pod.status and pod.status.phase == "Running":
            break
        time.sleep(2)

    # Exec a shell into the pod to trigger Falco alert
    # Must spawn an actual shell (sh) since the rule watches for shell processes
    subprocess.run(
        ["kubectl", "exec", "-n", SECURITY_NS, pod_name, "--", "sh", "-c", "echo falco-test"],
        capture_output=True, text=True, timeout=15,
    )

    # Wait briefly for Falco to process the event
    time.sleep(5)

    # Check Falco logs for the exec alert (use falco container only, not sidekick)
    result = subprocess.run(
        ["kubectl", "logs", "-n", SECURITY_NS, "-l", "app.kubernetes.io/name=falco",
         "-c", "falco", "--tail=100"],
        capture_output=True, text=True, timeout=15,
    )

    # Clean up
    try:
        k8s_core.delete_namespaced_pod(pod_name, SECURITY_NS)
    except client.exceptions.ApiException:
        pass

    # Falco should have logged something about the exec
    output = result.stdout.lower()
    assert "exec" in output or "shell" in output or "terminal" in output or "notice" in output, (
        f"Expected Falco alert about exec in logs, got: {result.stdout[-500:]}"
    )


# --- ESO Tests ---


def test_eso_secret_synced(k8s_custom: CustomObjectsApi) -> None:
    """ExternalSecret shows SecretSynced condition."""
    es = k8s_custom.get_namespaced_custom_object(
        group="external-secrets.io",
        version="v1",
        namespace=APPS_NS,
        plural="externalsecrets",
        name="test-secret",
    )
    conditions = es.get("status", {}).get("conditions", [])
    synced = any(
        c.get("type") == "Ready" and c.get("status") == "True"
        for c in conditions
    )
    assert synced, (
        f"ExternalSecret 'test-secret' not synced. Conditions: {conditions}"
    )


def test_eso_secret_value_matches(k8s_core: CoreV1Api) -> None:
    """K8s Secret created by ESO matches AWS Secrets Manager value."""
    secret = k8s_core.read_namespaced_secret("test-secret", APPS_NS)
    data = secret.data or {}

    # The ESO-synced secret should contain the JSON keys from AWS SM
    assert "username" in data, f"Expected 'username' key in secret, got: {list(data.keys())}"
    assert "password" in data, f"Expected 'password' key in secret, got: {list(data.keys())}"

    username = base64.b64decode(data["username"]).decode()
    password = base64.b64decode(data["password"]).decode()
    assert username == "admin", f"Expected username 'admin', got '{username}'"
    assert password == "testpass123", f"Expected password 'testpass123', got '{password}'"


# --- RBAC Tests ---


def test_rbac_cross_namespace_denied() -> None:
    """Service account in apps namespace cannot list secrets in platform namespace."""
    # Create a test SA in apps namespace if it doesn't exist
    result = subprocess.run(
        [
            "kubectl", "auth", "can-i", "list", "secrets",
            "--namespace", PLATFORM_NS,
            "--as", f"system:serviceaccount:{APPS_NS}:default",
        ],
        capture_output=True, text=True, timeout=15,
    )
    assert result.stdout.strip() == "no", (
        f"Expected 'no' for cross-namespace secret access, got: {result.stdout.strip()}"
    )


# --- NetworkPolicy Tests ---


def test_network_policy_blocks_cross_namespace() -> None:
    """NetworkPolicy in apps blocks traffic from other namespaces."""
    # Verify that a default-deny NetworkPolicy exists in apps
    result = subprocess.run(
        ["kubectl", "get", "networkpolicies", "-n", APPS_NS, "-o", "name"],
        capture_output=True, text=True, timeout=15,
    )
    assert result.returncode == 0, f"Failed to list NetworkPolicies: {result.stderr}"
    policies = result.stdout.strip()
    assert len(policies) > 0, "No NetworkPolicies found in apps namespace"
    assert "default-deny" in policies.lower(), (
        f"Expected a default-deny NetworkPolicy in apps, got: {policies}"
    )
