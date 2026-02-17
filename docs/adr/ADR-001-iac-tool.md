# ADR-001: Infrastructure as Code Tool

## Status

Accepted

## Context

We need to provision an EKS cluster with VPC, IAM roles, managed addons, and
networking configuration. The IaC tool must support the full AWS EKS lifecycle
including Pod Identity, managed addons, and access entries (replacing the
deprecated aws-auth ConfigMap).

## Decision

Use **Terraform** with the `terraform-aws-modules/eks/aws` module pinned to
`~>21.0` and the `terraform-aws-modules/vpc/aws` module for networking.

Key configuration:
- EKS 1.34+ with `authentication_mode = "API"` (v21 default)
- Access entries for IAM principal mapping (replaces aws-auth)
- Managed node group: 2x m7i.xlarge (current-gen Intel)
- Pod Identity as primary IAM mechanism for workloads
- Managed addons via Terraform: VPC CNI, CoreDNS, kube-proxy, Pod Identity
  Agent, EBS CSI Driver, AWS Load Balancer Controller
- VPC CNI with `enableNetworkPolicy = "true"` (native NetworkPolicy, no Calico)
- Local state backend (demo project, not team workflow)

## Consequences

**Easier:**
- Declarative, reproducible infrastructure
- Module ecosystem handles complex IAM and networking
- State management tracks drift
- Plan/apply workflow catches errors before provisioning

**Harder:**
- EKS module v21 removed aws-auth; must use access entries API
- IAM role chaining for Pod Identity can be finicky to debug
- Terraform state is local-only (acceptable for demo, not for production)
- If Terraform EKS module fights back on IAM, fallback to eksctl for cluster
  creation with Terraform for VPC/IAM only

## Alternatives Considered

- **eksctl**: Simpler for basic clusters but less flexible for VPC customization,
  addon configuration, and IAM role management. Kept as fallback.
- **Pulumi**: Strong programmatic model but smaller module ecosystem for AWS EKS.
  Less familiar to the target audience (platform engineers).
- **CloudFormation**: Verbose, slower iteration cycle, no plan preview equivalent.
  Rejected for developer experience reasons.
- **CDK**: Adds a compilation step and abstraction layer. Unnecessary complexity
  for a straightforward EKS deployment.
