# Scripts

Lifecycle management scripts for the KubeAuto Day IDP platform.

## Rebuild (Zero → Running)

```bash
export GITHUB_TOKEN=ghp_your_token_here
./scripts/rebuild.sh
```

**Time:** ~45 minutes (20 min Terraform + 5 min ArgoCD + 20 min full sync)

**What it does:**
1. Pre-flight checks (tools, AWS creds, GitHub token)
2. `terraform apply` — EKS cluster, VPC, IAM, LB Controller
3. Configure kubectl
4. Install ArgoCD via Helm
5. Create ArgoCD repo secret (private repo access)
6. Patch Dex GitHub OAuth credentials (from AWS Secrets Manager)
7. Create Backstage secrets (from AWS Secrets Manager)
8. Apply app-of-apps (bootstraps all 27 ArgoCD applications)
9. Wait for all apps to sync and become Healthy
10. Update Backstage K8s token (post-sync)

**Manual steps after rebuild:**
- Update DNS CNAME in Namecheap (ALB hostname changes)
- Verify GitHub OAuth callback URLs

**Prerequisites preserved across teardown/rebuild:**
- AWS Secrets Manager: `kubeauto/github-oauth`, `kubeauto/backstage-github-oauth`,
  `kubeauto/argocd-backstage-token`, `kubeauto/test-secret`
- ECR repositories (container images)
- GitHub OAuth App (persists in GitHub settings)
- DNS records (persist in Namecheap)

## Teardown (Running → Zero)

```bash
./scripts/teardown.sh
```

**Time:** ~15 minutes

**What it does:**
1. Deletes ArgoCD applications (removes finalizers if stuck)
2. Deletes ingresses and load balancers (unblocks VPC deletion)
3. Uninstalls Helm releases
4. `terraform destroy` — all AWS infrastructure
5. Verifies cleanup (EKS, NAT, EC2, EBS, ALBs)

**What it preserves:**
- AWS Secrets Manager secrets (needed for rebuild)
- ECR repositories (container images)
- Terraform state file (local, for reference)

**Cost after teardown:** $0/hr recurring. Small ECR storage charges only.
