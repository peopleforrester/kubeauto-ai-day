# ABOUTME: Shared pytest fixtures for IDP integration tests.
# ABOUTME: Provides Kubernetes client, AWS clients, and namespace configuration.

import pytest
import botocore.client

from kubernetes import client, config
from kubernetes.client import CoreV1Api
import boto3


# --- Short-name aliases for convenience ---
# Tests can use either the long name (k8s_core_v1) or short name (k8s_core).


@pytest.fixture(scope="session")
def k8s_core(k8s_core_v1: CoreV1Api) -> CoreV1Api:
    """Short alias for k8s_core_v1."""
    return k8s_core_v1


@pytest.fixture(scope="session")
def k8s_apps(k8s_apps_v1: client.AppsV1Api) -> client.AppsV1Api:
    """Short alias for k8s_apps_v1."""
    return k8s_apps_v1


@pytest.fixture(scope="session")
def k8s_custom(k8s_custom_objects: client.CustomObjectsApi) -> client.CustomObjectsApi:
    """Short alias for k8s_custom_objects."""
    return k8s_custom_objects


@pytest.fixture(scope="session")
def k8s_rbac(k8s_rbac_v1: client.RbacAuthorizationV1Api) -> client.RbacAuthorizationV1Api:
    """Short alias for k8s_rbac_v1."""
    return k8s_rbac_v1


@pytest.fixture(scope="session")
def boto_ec2() -> botocore.client.BaseClient:
    """Return an EC2 client for security group assertions."""
    return boto3.client("ec2", region_name="us-west-2")


# --- Full-name fixtures ---


@pytest.fixture(scope="session")
def k8s_core_v1() -> CoreV1Api:
    """Load kubeconfig and return a CoreV1Api client.

    Fails explicitly if no cluster is reachable (Rule G3: no fallbacks).
    """
    config.load_kube_config()
    return client.CoreV1Api()


@pytest.fixture(scope="session")
def k8s_apps_v1() -> client.AppsV1Api:
    """Return an AppsV1Api client for deployment/daemonset assertions."""
    config.load_kube_config()
    return client.AppsV1Api()


@pytest.fixture(scope="session")
def k8s_custom_objects() -> client.CustomObjectsApi:
    """Return a CustomObjectsApi client for CRD assertions."""
    config.load_kube_config()
    return client.CustomObjectsApi()


@pytest.fixture(scope="session")
def k8s_rbac_v1() -> client.RbacAuthorizationV1Api:
    """Return an RbacAuthorizationV1Api client for RBAC assertions."""
    config.load_kube_config()
    return client.RbacAuthorizationV1Api()


@pytest.fixture(scope="session")
def k8s_networking_v1() -> client.NetworkingV1Api:
    """Return a NetworkingV1Api client for ingress/network policy assertions."""
    config.load_kube_config()
    return client.NetworkingV1Api()


@pytest.fixture(scope="session")
def boto_secrets_manager() -> botocore.client.BaseClient:
    """Return a Secrets Manager client for ESO test assertions."""
    return boto3.client("secretsmanager", region_name="us-west-2")


@pytest.fixture(scope="session")
def boto_eks() -> botocore.client.BaseClient:
    """Return an EKS client for cluster configuration assertions."""
    return boto3.client("eks", region_name="us-west-2")


@pytest.fixture(scope="session")
def expected_namespaces() -> list[str]:
    """Return the list of namespaces the IDP platform requires."""
    return ["platform", "argocd", "monitoring", "backstage", "apps", "security", "kyverno", "cert-manager"]


@pytest.fixture(scope="session")
def cluster_name() -> str:
    """Return the EKS cluster name used throughout tests."""
    return "kubeauto-ai-day"
