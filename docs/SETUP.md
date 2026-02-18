# Setup Guide

Step-by-step instructions to reproduce this IDP from scratch.

## Prerequisites

### AWS

- AWS account with admin-level IAM permissions
- AWS CLI v2 configured (`aws configure`)
- Region: `us-west-2` (configurable in `infrastructure/terraform/variables.tf`)
- Budget: ~$0.57/hr while running (see [COST.md](COST.md))

### Tools

Install the following on your workstation:

| Tool | Version | Purpose |
|------|---------|---------|
| terraform | >= 1.7 | Infrastructure provisioning |
| kubectl | >= 1.34 | Kubernetes CLI |
| helm | >= 3.14 | Chart management |
| aws-cli | v2 | AWS API access |
| git | >= 2.x | Version control |
| python | >= 3.12 | Test runner |
| uv | >= 0.6 | Python package manager |
| gitleaks | >= 8.x | Secret scanning |

### Optional Tools

| Tool | Purpose |
|------|---------|
| argocd CLI | ArgoCD management (port-forward alternative) |
| k9s | Terminal UI for Kubernetes |

## Step 1: Clone the Repository

```bash
git clone git@github.com:peopleforrester/kubeauto-ai-day.git
cd kubeauto-ai-day
git checkout staging
```

## Step 2: Provision Infrastructure

```bash
cd infrastructure/terraform

# Review the plan
terraform init
terraform plan

# Apply (creates VPC, EKS cluster, IAM roles, managed addons, LB controller)
terraform apply

# Configure kubectl
aws eks update-kubeconfig --name kubeauto-ai-day --region us-west-2
```

This creates:
- VPC with 3 AZs (public + private subnets, single NAT gateway)
- EKS 1.34 cluster with 2x m7i.xlarge nodes
- Managed addons: VPC CNI (with NetworkPolicy), CoreDNS, kube-proxy, Pod Identity Agent, EBS CSI
- IAM roles: EBS CSI (IRSA), AWS LB Controller (IRSA)
- AWS Load Balancer Controller (Helm)

Estimated time: 15-20 minutes.

## Step 3: Verify Cluster

```bash
kubectl get nodes
# Should show 2 nodes in Ready state

kubectl get pods -A
# Should show kube-system pods + LB controller running
```

## Step 4: Create AWS Secrets

Before deploying the security stack, create the required secrets in AWS
Secrets Manager:

```bash
# ESO test secret (for validation)
aws secretsmanager create-secret \
  --name kubeauto/test-secret \
  --secret-string '{"username":"testuser","password":"testpass123"}' \
  --region us-west-2

# GitHub OAuth credentials (for OIDC — optional)
aws secretsmanager create-secret \
  --name kubeauto/github-oauth \
  --secret-string '{"clientID":"your-github-oauth-client-id","clientSecret":"your-github-oauth-client-secret"}' \
  --region us-west-2
```

## Step 5: Bootstrap ArgoCD

ArgoCD is installed via Helm in Terraform, then manages itself and all
subsequent applications.

```bash
# ArgoCD is already installed by Terraform's helm_release
# Verify it's running:
kubectl get pods -n argocd

# Get the initial admin password:
kubectl get secret argocd-initial-admin-secret -n argocd \
  -o jsonpath='{.data.password}' | base64 -d

# Port-forward to access UI:
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Open https://localhost:8080, login as admin
```

## Step 6: Deploy App-of-Apps

```bash
# Create the repo secret for private GitHub access:
kubectl create secret generic repo-kubeauto \
  --namespace argocd \
  --from-literal=type=git \
  --from-literal=url=https://github.com/peopleforrester/kubeauto-ai-day.git \
  --from-literal=username=git \
  --from-literal=password=<YOUR_GITHUB_PAT> \
  --dry-run=client -o yaml | kubectl apply -f -

# Label it for ArgoCD discovery:
kubectl label secret repo-kubeauto -n argocd \
  argocd.argoproj.io/secret-type=repository

# Apply the root Application:
kubectl apply -f gitops/root-app.yaml
```

ArgoCD will now discover and sync all 20 child Applications via the
app-of-apps pattern. Sync waves ensure correct ordering.

## Step 7: Watch the Deployment

```bash
# Watch all Applications sync:
kubectl get applications -n argocd -w

# Or use the ArgoCD UI (port-forward on 8080)
```

Expected sync order (by wave):
1. Namespaces (wave -10)
2. Kyverno, cert-manager (wave -5)
3. Falco, ESO (wave -3)
4. Falcosidekick, ESO resources (wave -1)
5. Prometheus, RBAC, NetworkPolicies, dashboards (wave 0)
6. OTel, cert-manager issuers (wave 1)
7. Kyverno policies, quotas (wave 2)
8. Sample app, Backstage (wave 5)

Full deployment takes approximately 5-8 minutes.

## Step 8: Verify Everything

```bash
# Install test dependencies:
uv sync

# Run the full test suite:
uv run pytest tests/ -v

# Expected: 59 tests passing
```

### Access Platform UIs

```bash
# ArgoCD (GitOps)
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Grafana (Observability)
kubectl port-forward svc/prometheus-grafana -n monitoring 3000:80
# Default creds: admin / prom-operator

# Backstage (Developer Portal)
kubectl port-forward svc/backstage -n backstage 7007:7007
```

## Verification Commands

Quick health check for all components:

```bash
# All pods healthy
kubectl get pods -A --field-selector status.phase!=Running,status.phase!=Succeeded

# All ArgoCD apps synced
kubectl get applications -n argocd -o custom-columns=NAME:.metadata.name,SYNC:.status.sync.status,HEALTH:.status.health.status

# Kyverno policies active
kubectl get clusterpolicies

# Falco running
kubectl get pods -n security -l app.kubernetes.io/name=falco

# Secrets synced
kubectl get externalsecrets -A

# Certificates ready
kubectl get clusterissuers
```

## Troubleshooting

### ArgoCD Application stuck in "Progressing"

```bash
# Force refresh from Git:
kubectl patch application <app-name> -n argocd \
  --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'
```

### Kyverno blocking system pods

Kyverno policies only enforce in the `apps` namespace. If you see unexpected
blocks, check the namespace — all system namespaces are excluded.

### OTel Collector CrashLoopBackOff

Verify the image is `contrib` (not `k8s`): the k8s image lacks the
prometheusremotewrite exporter.

### cert-manager not syncing

Ensure the cert-manager namespace exists (sync wave -10 must complete
before wave -5).
