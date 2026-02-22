# Infrastructure

EKS cluster and supporting AWS resources, managed with Terraform.

## Directory Structure

```
terraform/
  main.tf           # Provider config, backend, data sources
  vpc.tf            # VPC with 3 AZs, public/private subnets, NAT gateway
  eks.tf            # EKS 1.34 cluster, managed node group, addons
  iam.tf            # IRSA roles for EBS CSI, LB Controller, ESO
  secrets.tf        # AWS Secrets Manager test secret
  variables.tf      # Input variables (cluster name, region, sizing)
  outputs.tf        # Cluster endpoint, OIDC provider, VPC ID
```

## Prerequisites

- AWS account with admin access
- Terraform >= 1.7
- AWS CLI configured (`aws sts get-caller-identity` should succeed)
- kubectl
- Helm 3.x

## Usage

```bash
cd infrastructure/terraform
terraform init
terraform plan -out=plan.out
terraform apply plan.out
```

After apply, configure kubectl:

```bash
aws eks update-kubeconfig --name kubeauto-idp --region eu-west-1
```

## Key Design Decisions

- **EKS module ~>21.0**: Uses API authentication mode (no aws-auth ConfigMap)
- **m7i.xlarge nodes**: Current-gen Intel, good price-performance for demo
- **Single NAT gateway**: Cost optimization for demo (not HA)
- **Pod Identity primary**: IRSA fallback for addons that don't support Pod Identity
- **Managed EKS addons**: VPC CNI, CoreDNS, kube-proxy, EBS CSI via Terraform (not Helm)
- **VPC CNI network policy**: Enabled for Kubernetes NetworkPolicy support

See [ADR-001](../docs/adr/ADR-001-iac-tool.md) for the Terraform selection rationale.

## Terraform State

State files (`.tfstate`) and variable files (`.tfvars`) are gitignored.
For this demo, state is stored locally. Production would use S3 + DynamoDB backend.
