# Teardown Guide

Step-by-step instructions to destroy the platform and stop all AWS charges.

## Pre-Teardown Checklist

- [ ] Export any data you want to keep (Grafana dashboards, Prometheus metrics)
- [ ] Note down any screenshots needed for the talk
- [ ] Confirm you don't need the cluster anymore

## Step 1: Delete ArgoCD Applications

Remove ArgoCD's finalizers first to prevent it from blocking Terraform destroy.

```bash
# Delete the root app-of-apps (cascades to all child apps):
kubectl delete application root-app -n argocd --cascade=foreground

# Wait for all applications to be deleted:
kubectl get applications -n argocd
# Should return: No resources found

# If any applications are stuck, remove their finalizers:
for app in $(kubectl get applications -n argocd -o name); do
  kubectl patch $app -n argocd --type json \
    -p '[{"op":"remove","path":"/metadata/finalizers"}]'
done
```

## Step 2: Delete Helm Releases

```bash
# Remove ArgoCD (installed by Terraform but managed by itself):
helm uninstall argocd -n argocd 2>/dev/null || true

# Remove AWS LB Controller:
helm uninstall aws-load-balancer-controller -n kube-system 2>/dev/null || true
```

## Step 3: Clean Up Kubernetes Resources

```bash
# Delete any remaining Load Balancers (these block VPC destruction):
kubectl delete ingress --all -A
kubectl delete svc --all-services --field-selector spec.type=LoadBalancer -A

# Wait for Load Balancers to be fully removed (check AWS console or):
aws elbv2 describe-load-balancers --query 'LoadBalancers[?contains(LoadBalancerName, `kubeauto`)]' --region us-west-2
```

## Step 4: Terraform Destroy

```bash
cd infrastructure/terraform

# Review what will be destroyed:
terraform plan -destroy

# Destroy all infrastructure:
terraform destroy

# Confirm with "yes" when prompted
```

Estimated time: 10-15 minutes.

## Step 5: Clean Up AWS Resources

Some resources may not be managed by Terraform:

```bash
# Delete Secrets Manager secrets (created manually):
aws secretsmanager delete-secret --secret-id kubeauto/test-secret --force-delete-without-recovery --region us-west-2
aws secretsmanager delete-secret --secret-id kubeauto/github-oauth --force-delete-without-recovery --region us-west-2

# Verify no orphaned EBS volumes:
aws ec2 describe-volumes --filters "Name=tag:kubernetes.io/cluster/kubeauto-ai-day,Values=owned" --region us-west-2

# Delete any orphaned EBS volumes:
# aws ec2 delete-volume --volume-id vol-xxx --region us-west-2

# Verify no orphaned ENIs:
aws ec2 describe-network-interfaces --filters "Name=tag:cluster.k8s.amazonaws.com/name,Values=kubeauto-ai-day" --region us-west-2

# Verify no orphaned Security Groups (beyond default):
aws ec2 describe-security-groups --filters "Name=tag:kubernetes.io/cluster/kubeauto-ai-day,Values=owned" --region us-west-2
```

## Step 6: Verify Cost Stop

```bash
# Check for any remaining EC2 instances:
aws ec2 describe-instances --filters "Name=tag:eks:cluster-name,Values=kubeauto-ai-day" "Name=instance-state-name,Values=running" --region us-west-2

# Check for NAT Gateways (these cost money):
aws ec2 describe-nat-gateways --filter "Name=tag:Name,Values=*kubeauto*" --region us-west-2

# Check for EKS cluster:
aws eks describe-cluster --name kubeauto-ai-day --region us-west-2 2>/dev/null && echo "CLUSTER STILL EXISTS" || echo "Cluster deleted"
```

## Expected Cost After Teardown

After a clean teardown, no recurring AWS charges should remain.

If you kept the Secrets Manager secrets without `--force-delete-without-recovery`,
they enter a 7-30 day recovery window and still incur a small charge
($0.40/secret/month).

## Common Teardown Issues

### Terraform destroy fails on VPC

Usually caused by orphaned Load Balancers or ENIs. Run the cleanup commands
in Step 5 and retry.

### EKS cluster stuck in "Deleting"

Check for orphaned nodegroups:
```bash
aws eks list-nodegroups --cluster-name kubeauto-ai-day --region us-west-2
```

### Security Groups can't be deleted

Usually caused by ENIs still attached. Wait 5 minutes and retry, or
manually detach ENIs first.
