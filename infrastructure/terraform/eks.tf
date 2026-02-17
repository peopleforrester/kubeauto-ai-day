# ABOUTME: EKS cluster configuration using terraform-aws-modules/eks/aws v21+.
# ABOUTME: Configures EKS 1.34+, managed addons, Pod Identity, and node groups.

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.0"

  # v21.15+: uses `name` and `kubernetes_version` (not cluster_name/cluster_version)
  name               = var.cluster_name
  kubernetes_version  = var.cluster_version

  # v21 default: API-only authentication (no aws-auth ConfigMap)
  authentication_mode = "API"

  # Network configuration
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  # API endpoint access — private + public for demo
  endpoint_private_access = true
  endpoint_public_access  = true

  # Enable control plane logging
  enabled_log_types = [
    "api", "audit", "authenticator", "controllerManager", "scheduler"
  ]

  # Access entries — replace aws-auth (removed in module v21)
  enable_cluster_creator_admin_permissions = true

  # IRSA — needed for EBS CSI and LB Controller service account roles
  enable_irsa = true

  # Managed addons — via Terraform, NOT Helm
  addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
      configuration_values = jsonencode({
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
      most_recent             = true
      service_account_role_arn = module.ebs_csi_irsa.iam_role_arn
    }
  }

  # Managed node group — m7i.xlarge (current-gen Intel)
  eks_managed_node_groups = {
    default = {
      instance_types = var.node_instance_types
      min_size       = var.node_min_size
      max_size       = var.node_max_size
      desired_size   = var.node_desired_size

      # Use AL2023 AMI (default for EKS 1.34+)
      ami_type = "AL2023_x86_64_STANDARD"
    }
  }
}
