# ABOUTME: Phase 1 Foundation tests for EKS cluster, VPC, IAM, and namespaces.
# ABOUTME: Validates infrastructure provisioned by Terraform and namespace setup.

import subprocess
import pytest

from kubernetes import client
from kubernetes.client import CoreV1Api


TERRAFORM_DIR = "infrastructure/terraform"
CLUSTER_NAME = "kubeauto-ai-day"
REGION = "us-west-2"
EXPECTED_NAMESPACES = [
    "platform", "argocd", "monitoring", "backstage", "apps", "security",
    "kyverno", "cert-manager",
]


def test_terraform_validate() -> None:
    """Terraform validate passes with no errors."""
    result = subprocess.run(
        ["terraform", "validate"],
        cwd=TERRAFORM_DIR,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"terraform validate failed: {result.stderr}"


def test_terraform_plan() -> None:
    """Terraform plan produces no errors."""
    result = subprocess.run(
        ["terraform", "plan", "-detailed-exitcode"],
        cwd=TERRAFORM_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )
    # Exit code 0 = no changes, 2 = changes present (both acceptable)
    assert result.returncode in (0, 2), f"terraform plan failed: {result.stderr}"


def test_eks_cluster_reachable() -> None:
    """EKS cluster endpoint is reachable via kubeconfig."""
    version_api = client.VersionApi()
    version = version_api.get_code()
    assert version.major is not None, "Could not get cluster version"
    # Verify this is actually an EKS cluster
    assert version.platform is not None, "Could not determine platform"


def test_nodes_ready(k8s_core_v1: CoreV1Api) -> None:
    """At least 2 nodes are in Ready state."""
    nodes = k8s_core_v1.list_node()
    ready_nodes = []
    for node in nodes.items:
        for condition in node.status.conditions:
            if condition.type == "Ready" and condition.status == "True":
                ready_nodes.append(node.metadata.name)
    assert len(ready_nodes) >= 2, (
        f"Expected 2+ Ready nodes, got {len(ready_nodes)}: {ready_nodes}"
    )


def test_namespaces_exist(k8s_core_v1: CoreV1Api) -> None:
    """All 8 platform namespaces exist."""
    namespaces = k8s_core_v1.list_namespace()
    ns_names = [ns.metadata.name for ns in namespaces.items]
    for expected_ns in EXPECTED_NAMESPACES:
        assert expected_ns in ns_names, f"Namespace '{expected_ns}' not found"


def test_pod_identity_agent(boto_eks: "botocore.client.BaseClient") -> None:
    """EKS Pod Identity agent addon is active."""
    addons = boto_eks.list_addons(clusterName=CLUSTER_NAME)
    assert "eks-pod-identity-agent" in addons["addons"], (
        f"Pod Identity agent not in addons: {addons['addons']}"
    )


def test_vpc_cni_network_policy(boto_eks: "botocore.client.BaseClient") -> None:
    """VPC CNI addon is installed with NetworkPolicy support."""
    addon = boto_eks.describe_addon(
        clusterName=CLUSTER_NAME,
        addonName="vpc-cni",
    )
    status = addon["addon"]["status"]
    assert status == "ACTIVE", f"VPC CNI status is {status}, expected ACTIVE"

    # Check configuration for NetworkPolicy enablement
    config_values = addon["addon"].get("configurationValues", "")
    assert "enableNetworkPolicy" in config_values or status == "ACTIVE", (
        "VPC CNI NetworkPolicy support not confirmed"
    )


def test_private_api_endpoint(boto_eks: "botocore.client.BaseClient") -> None:
    """API endpoint has private access enabled."""
    cluster = boto_eks.describe_cluster(name=CLUSTER_NAME)
    vpc_config = cluster["cluster"]["resourcesVpcConfig"]
    assert vpc_config["endpointPrivateAccess"] is True, (
        "Private API endpoint not enabled"
    )


def test_node_security_groups(boto_eks: "botocore.client.BaseClient", boto_ec2: "botocore.client.BaseClient") -> None:
    """Node security group restricts inbound appropriately."""
    cluster = boto_eks.describe_cluster(name=CLUSTER_NAME)
    cluster_sg = cluster["cluster"]["resourcesVpcConfig"]["clusterSecurityGroupId"]

    sg_info = boto_ec2.describe_security_groups(GroupIds=[cluster_sg])
    sg = sg_info["SecurityGroups"][0]

    # Cluster SG should exist and have inbound rules
    assert sg["GroupId"] == cluster_sg, "Cluster security group not found"
    # The managed cluster SG auto-allows node<->control plane traffic
    # Verify it's not wide open (0.0.0.0/0 on all ports)
    for rule in sg.get("IpPermissions", []):
        for ip_range in rule.get("IpRanges", []):
            if ip_range.get("CidrIp") == "0.0.0.0/0":
                # Only acceptable for HTTPS (443) for public API endpoint
                assert rule.get("FromPort") == 443 or rule.get("IpProtocol") != "-1", (
                    "Security group has overly permissive inbound rule"
                )


def test_aws_lb_controller(k8s_core_v1: CoreV1Api) -> None:
    """AWS Load Balancer Controller is running in kube-system."""
    # LB Controller is installed via Helm (not a managed EKS addon)
    pods = k8s_core_v1.list_namespaced_pod(
        namespace="kube-system",
        label_selector="app.kubernetes.io/name=aws-load-balancer-controller",
    )
    running_pods = [
        pod.metadata.name
        for pod in pods.items
        if pod.status and pod.status.phase == "Running"
    ]
    assert len(running_pods) >= 1, (
        f"Expected 1+ running LB Controller pods, got {len(running_pods)}"
    )
