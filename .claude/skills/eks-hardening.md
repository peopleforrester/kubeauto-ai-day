# EKS Hardening Skill — KubeAuto Day IDP

This skill encodes the correct patterns for provisioning and hardening EKS 1.34+
using the Terraform AWS EKS module v21+. It prevents generation of deprecated
aws-auth ConfigMap patterns, IRSA-first IAM, or unmanaged addons.

---

## Correct Patterns

### Terraform EKS Module v21+ (aws-auth removed)

Module v21 removed the `aws-auth` ConfigMap management entirely. Cluster access
is now controlled exclusively via the EKS Access API (`authentication_mode = "API"`).

```hcl
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.0"

  cluster_name    = "kubeauto-day"
  cluster_version = "1.34"

  # v21 default: API-only authentication (no aws-auth ConfigMap)
  authentication_mode = "API"

  # Access entries replace aws-auth mapRoles/mapUsers
  access_entries = {
    admin = {
      principal_arn = "arn:aws:iam::123456789012:role/AdminRole"
      policy_associations = {
        admin = {
          policy_arn = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"
          access_scope = {
            type = "cluster"
          }
        }
      }
    }
  }

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  # Private API endpoint, public disabled for production
  cluster_endpoint_private_access = true
  cluster_endpoint_public_access  = true  # true for demo; false for production

  # Managed node group — m7i.xlarge, NOT m5.xlarge
  eks_managed_node_groups = {
    default = {
      instance_types = ["m7i.xlarge"]
      min_size       = 2
      max_size       = 4
      desired_size   = 3

      # Pod Identity agent is installed as a managed addon (see below)
      # Node IAM role gets Pod Identity association permissions automatically
    }
  }

  # Enable encryption of secrets at rest
  cluster_encryption_config = {
    provider_key_arn = aws_kms_key.eks.arn
    resources        = ["secrets"]
  }

  # Enable control plane logging
  cluster_enabled_log_types = [
    "api", "audit", "authenticator", "controllerManager", "scheduler"
  ]

  tags = local.tags
}
```

### Pod Identity (Primary IAM Pattern)

Pod Identity is the primary IAM mechanism. IRSA is fallback only for addons
that have not yet adopted Pod Identity (check addon docs individually).

```hcl
# Pod Identity agent addon — required for Pod Identity to work
module "eks" {
  # ... (inside the eks module block)
  cluster_addons = {
    eks-pod-identity-agent = {
      most_recent = true
    }
    # Other managed addons below
  }
}

# Pod Identity association for a workload
resource "aws_eks_pod_identity_association" "external_secrets" {
  cluster_name    = module.eks.cluster_name
  namespace       = "security"
  service_account = "external-secrets-sa"
  role_arn        = module.external_secrets_irsa.iam_role_arn
}

# IAM role for Pod Identity (trust policy differs from IRSA)
module "external_secrets_pod_identity" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.0"

  role_name = "external-secrets-pod-identity"

  # Pod Identity trust policy — trusts pods.eks.amazonaws.com
  # NOT oidc.eks (that is IRSA)
  attach_external_secrets_policy = true
}
```

### Managed Addons via Terraform (NOT Helm)

All core EKS addons are managed through the Terraform EKS module, not Helm charts.

```hcl
cluster_addons = {
  coredns = {
    most_recent = true
    configuration_values = jsonencode({
      tolerations = [{
        key      = "CriticalAddonsOnly"
        operator = "Exists"
      }]
    })
  }
  kube-proxy = {
    most_recent = true
  }
  vpc-cni = {
    most_recent = true
    configuration_values = jsonencode({
      # Enable NetworkPolicy support in VPC CNI
      enableNetworkPolicy = "true"
      env = {
        ENABLE_PREFIX_DELEGATION = "true"
      }
    })
  }
  eks-pod-identity-agent = {
    most_recent = true
  }
  aws-ebs-csi-driver = {
    most_recent            = true
    service_account_role_arn = module.ebs_csi_pod_identity.iam_role_arn
  }
}
```

### VPC CNI with NetworkPolicy Support

The VPC CNI plugin natively supports Kubernetes NetworkPolicy as of v1.14+.
Enable it via the addon configuration; do NOT install Calico or Cilium separately.

```hcl
# In cluster_addons (shown above):
vpc-cni = {
  most_recent = true
  configuration_values = jsonencode({
    enableNetworkPolicy = "true"
  })
}
```

### Security Group Rules

```hcl
# Restrict node-to-node traffic to required ports only
resource "aws_security_group_rule" "node_to_node" {
  type                     = "ingress"
  from_port                = 0
  to_port                  = 65535
  protocol                 = "tcp"
  security_group_id        = module.eks.node_security_group_id
  source_security_group_id = module.eks.node_security_group_id
  description              = "Node-to-node communication"
}

# Restrict API server access to VPC CIDR
resource "aws_security_group_rule" "api_private" {
  type              = "ingress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  security_group_id = module.eks.cluster_security_group_id
  cidr_blocks       = [module.vpc.vpc_cidr_block]
  description       = "Private API endpoint access from VPC"
}
```

### PSS Labels on `apps` Namespace

Pod Security Standards labels provide defense-in-depth alongside Kyverno enforce policies.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: apps
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

---

## Guardrail Integration

EKS infrastructure implements **Guardrails #2 and #7** at Layer 3 (Kubernetes Infrastructure).

| Guardrail | How EKS Implements It |
|-----------|----------------------|
| **#2 Blast Radius Limits** | VPC isolation (private subnets, NAT gateway). Security groups restrict node-to-node and API access. Private API endpoint. PSS labels on `apps` namespace. Managed node groups with defined instance types and scaling limits. |
| **#7 Secrets & Credential Isolation** | Pod Identity eliminates long-lived credentials. No static IAM keys. IRSA used only as fallback for specific addons. KMS encryption for secrets at rest. Control plane audit logging captures all API server actions. |

**Layer 2 enforcement:** The `cc-pretool-guard.sh` hook blocks `terraform destroy` without explicit confirmation and blocks write operations on `kube-system`.

**Layer 1 enforcement:** `terraform validate` and `terraform fmt` pre-commit hooks catch configuration errors before they reach the cluster.

---

### AWS Load Balancer Controller

Installed in Phase 1 for ingress support. Uses Pod Identity.

```hcl
module "aws_lb_controller_pod_identity" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.0"

  role_name                              = "aws-lb-controller"
  attach_load_balancer_controller_policy = true
}

resource "aws_eks_pod_identity_association" "aws_lb_controller" {
  cluster_name    = module.eks.cluster_name
  namespace       = "kube-system"
  service_account = "aws-load-balancer-controller"
  role_arn        = module.aws_lb_controller_pod_identity.iam_role_arn
}
```

---

## Common Mistakes

### CRITICAL: Do NOT use aws-auth ConfigMap

```hcl
# WRONG — aws-auth was removed in module v21
manage_aws_auth_configmap = true  # This parameter no longer exists
aws_auth_roles = [...]            # This parameter no longer exists
```

The module will fail with unknown variable errors. Use `access_entries` instead.

### CRITICAL: Do NOT use IRSA as the primary IAM pattern

```hcl
# WRONG — IRSA is the fallback pattern, not primary
enable_irsa = true  # Only enable if a specific addon requires it

# WRONG trust policy for Pod Identity
# IRSA trusts oidc.eks.amazonaws.com — Pod Identity trusts pods.eks.amazonaws.com
```

### Do NOT install addons via Helm when managed addons exist

```hcl
# WRONG — do not use Helm for core addons
resource "helm_release" "vpc_cni" {
  name       = "aws-vpc-cni"
  repository = "https://aws.github.io/eks-charts"
  # ...
}

# CORRECT — use the cluster_addons block inside the EKS module
```

### Do NOT use m5.xlarge

```hcl
# WRONG — m5 is previous generation
instance_types = ["m5.xlarge"]

# CORRECT — m7i is current generation
instance_types = ["m7i.xlarge"]
```

### Do NOT use authentication_mode = "API_AND_CONFIG_MAP"

```hcl
# WRONG for new clusters — dual mode is for migration only
authentication_mode = "API_AND_CONFIG_MAP"

# CORRECT for new clusters
authentication_mode = "API"
```

### Do NOT install Calico or Cilium for NetworkPolicy

The VPC CNI handles NetworkPolicy natively when `enableNetworkPolicy = "true"`.
Installing a separate CNI plugin causes conflicts.

### Do NOT hardcode EKS version to 1.31 or lower

```hcl
# WRONG — 1.31 is in extended support at 6x cost
cluster_version = "1.31"

# CORRECT
cluster_version = "1.34"
```

---

## Validation Commands

```bash
# Verify cluster version
aws eks describe-cluster --name kubeauto-day --query 'cluster.version'

# Verify authentication mode is API (not CONFIG_MAP)
aws eks describe-cluster --name kubeauto-day \
  --query 'cluster.accessConfig.authenticationMode'

# Verify Pod Identity agent addon is active
aws eks describe-addon --cluster-name kubeauto-day \
  --addon-name eks-pod-identity-agent --query 'addon.status'

# Verify VPC CNI NetworkPolicy support is enabled
kubectl get daemonset aws-node -n kube-system -o jsonpath='{.spec.template.spec.containers[0].env}' | \
  grep -i networkpolicy

# Verify managed addons (should list coredns, kube-proxy, vpc-cni, eks-pod-identity-agent)
aws eks list-addons --cluster-name kubeauto-day --query 'addons'

# Verify node instance type
kubectl get nodes -o jsonpath='{.items[*].metadata.labels.node\.kubernetes\.io/instance-type}'

# Verify secrets encryption
aws eks describe-cluster --name kubeauto-day \
  --query 'cluster.encryptionConfig[0].resources'

# Verify control plane logging
aws eks describe-cluster --name kubeauto-day \
  --query 'cluster.logging.clusterLogging[?enabled==`true`].types[]'

# Verify private endpoint is enabled
aws eks describe-cluster --name kubeauto-day \
  --query 'cluster.resourcesVpcConfig.endpointPrivateAccess'

# Verify PSS labels on apps namespace
kubectl get namespace apps -o jsonpath='{.metadata.labels}' | jq .

# Verify access entries exist (no aws-auth)
aws eks list-access-entries --cluster-name kubeauto-day

# Terraform validation
terraform validate
terraform plan -detailed-exitcode
```
