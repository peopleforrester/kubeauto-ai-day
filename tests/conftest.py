# ABOUTME: Shared pytest fixtures for IDP integration tests.
# ABOUTME: Provides Kubernetes client, AWS clients, and namespace configuration.

import pytest
from typing import Optional

from kubernetes import client, config
from kubernetes.client import CoreV1Api, ApiClient
import boto3


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
def boto_secrets_manager() -> boto3.client:
    """Return a Secrets Manager client for ESO test assertions."""
    return boto3.client("secretsmanager", region_name="us-west-2")


@pytest.fixture(scope="session")
def boto_eks() -> boto3.client:
    """Return an EKS client for cluster configuration assertions."""
    return boto3.client("eks", region_name="us-west-2")


@pytest.fixture(scope="session")
def expected_namespaces() -> list[str]:
    """Return the list of namespaces the IDP platform requires."""
    return ["platform", "argocd", "monitoring", "backstage", "apps", "security"]


@pytest.fixture(scope="session")
def cluster_name() -> str:
    """Return the EKS cluster name used throughout tests."""
    return "kubeauto-ai-day"
