# Phase 1: Foundation (Budget: 60 min)

**Goal:** EKS cluster running with VPC, IAM baseline, and kubeconfig working.

**Inputs:** Empty AWS account with admin credentials configured.

**Outputs:**
- Terraform config for VPC (3 AZ, public/private subnets, NAT gateway)
- Terraform config for EKS cluster (private API endpoint, managed node group)
- IAM roles for cluster, node group, and Pod Identity agent
- Working kubeconfig
- Namespace structure: platform, argocd, monitoring, backstage, apps, security

**Test Criteria (tests/test_phase_01_foundation.py):**
- terraform validate passes with no errors
- terraform plan produces no errors
- EKS cluster endpoint is reachable via kubeconfig
- kubectl get nodes returns at least 2 Ready nodes
- All defined namespaces exist
- EKS Pod Identity agent addon is active
- VPC CNI is running with NetworkPolicy support enabled
- Private API endpoint is enabled, public is disabled (or restricted to specific CIDR)
- Node security group restricts inbound to cluster SG only
- AWS Load Balancer Controller addon is active

**Completion Promise:** `<promise>PHASE1_DONE</promise>`

**Known Risk:** Terraform EKS module is notoriously finicky with IAM role chaining. If Claude gets stuck for more than 3 iterations on IAM, fall back to eksctl for cluster creation and Terraform for VPC/IAM only.

**Key Technology Decisions:**
- EKS: 1.34+
- Terraform EKS module: ~>21.0 (v21 removed aws-auth, API auth mode default)
- Instance type: m7i.xlarge (2 nodes)
- Pod Identity primary, IRSA fallback
- EKS managed addons via Terraform (VPC CNI, CoreDNS, kube-proxy, Pod Identity Agent, EBS CSI Driver)
- AWS Load Balancer Controller as EKS addon
- PSS labels on `apps` namespace

**ADR:** ADR-001 (IaC Tool: Terraform)
**Commits:** 2 (Terraform infra; Namespaces + tests)
