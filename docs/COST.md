# ABOUTME: AWS cost breakdown for the KubeAuto Day IDP cluster.
# ABOUTME: Includes hourly rates, projected monthly costs, and teardown instructions.

# AWS Cost Estimates

## Hourly Cost Breakdown

| Resource | Hourly Cost | Notes |
|----------|-------------|-------|
| EKS Control Plane | $0.10 | Standard support pricing (1.34+) |
| EC2 m7i.xlarge × 2 | $0.40 | 2 nodes × $0.2016/hr (us-west-2) |
| NAT Gateway | $0.045 | Single AZ, data processing extra |
| EBS gp3 volumes | ~$0.02 | PVCs for Prometheus, Grafana |
| ECR storage | <$0.01 | ~100MB sample app image |
| Secrets Manager | <$0.01 | 2 secrets × $0.40/mo |
| **Total** | **~$0.57/hr** | |

## Projected Costs

| Duration | Cost |
|----------|------|
| 10-hour build session | ~$5.70 |
| 24-hour cluster uptime | ~$13.70 |
| 1 week (168 hours) | ~$95.76 |
| 1 month (730 hours) | ~$416.10 |

## Cost Optimization Notes

- Extended support EKS versions (1.31 and older) cost $0.60/hr for control
  plane — 6× the standard rate. Always use standard support versions.
- NAT Gateway charges $0.045/hr + $0.045/GB processed. For a demo cluster
  with minimal egress, the hourly charge dominates.
- EBS gp3 volumes are $0.08/GB/month. Prometheus and Grafana PVCs total
  ~20GB = ~$1.60/month.
- Spot instances could reduce EC2 costs by ~60% but are not recommended
  for a demo platform due to interruption risk.

## Teardown Instructions

To destroy all AWS resources and stop costs:

```bash
# Remove ArgoCD applications first (prevents orphaned resources)
kubectl delete applications --all -n argocd

# Wait for cleanup
sleep 30

# Destroy Terraform-managed infrastructure
cd infrastructure/terraform
terraform destroy -auto-approve

# Verify no lingering resources
aws ec2 describe-instances --filters "Name=tag:kubernetes.io/cluster/kubeauto-idp,Values=owned" --query 'Reservations[].Instances[].InstanceId'
aws elbv2 describe-load-balancers --query 'LoadBalancers[?starts_with(LoadBalancerName, `k8s-`)].LoadBalancerArn'
```

Check the AWS billing console 24 hours after teardown to confirm all charges
have stopped.
