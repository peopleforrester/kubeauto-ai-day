#!/usr/bin/env bash
# ABOUTME: Automated teardown script for the KubeAuto Day IDP platform.
# ABOUTME: Cleanly destroys all Kubernetes and AWS resources to stop all charges.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TF_DIR="$REPO_ROOT/infrastructure/terraform"
REGION="us-west-2"
CLUSTER_NAME="kubeauto-ai-day"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()  { echo -e "${GREEN}[$(date +%H:%M:%S)]${NC} $*"; }
warn() { echo -e "${YELLOW}[$(date +%H:%M:%S)] WARNING:${NC} $*"; }
err()  { echo -e "${RED}[$(date +%H:%M:%S)] ERROR:${NC} $*" >&2; }
step() { echo -e "\n${BLUE}═══════════════════════════════════════════${NC}"; echo -e "${BLUE}  STEP $1: $2${NC}"; echo -e "${BLUE}═══════════════════════════════════════════${NC}\n"; }

# ─────────────────────────────────────────────────────────────────────
# Confirmation
# ─────────────────────────────────────────────────────────────────────
echo -e "${RED}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║  THIS WILL DESTROY THE ENTIRE PLATFORM           ║${NC}"
echo -e "${RED}║  EKS cluster, VPC, IAM roles, all resources      ║${NC}"
echo -e "${RED}║                                                   ║${NC}"
echo -e "${RED}║  AWS Secrets Manager secrets will be PRESERVED    ║${NC}"
echo -e "${RED}║  (needed for rebuild)                             ║${NC}"
echo -e "${RED}╚══════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Type ${RED}DESTROY${NC} to confirm: "
read -r CONFIRM
if [[ "$CONFIRM" != "DESTROY" ]]; then
    echo "Aborted."
    exit 1
fi

SECONDS=0

# ─────────────────────────────────────────────────────────────────────
# Step 1: Delete ArgoCD applications (remove finalizers)
# ─────────────────────────────────────────────────────────────────────
step "1" "Delete ArgoCD applications"

if kubectl get namespace argocd &>/dev/null 2>&1; then
    # Delete app-of-apps first
    log "Deleting app-of-apps (cascading to child apps)..."
    kubectl delete application app-of-apps -n argocd --timeout=120s 2>/dev/null || true

    # Wait for child apps to clear
    log "Waiting for applications to be deleted (up to 2 minutes)..."
    RETRIES=0
    while kubectl get applications -n argocd --no-headers 2>/dev/null | grep -q .; do
        RETRIES=$((RETRIES + 1))
        if [[ $RETRIES -gt 24 ]]; then
            warn "Some apps still exist after 2 minutes. Force-removing finalizers..."
            for app in $(kubectl get applications -n argocd -o name 2>/dev/null); do
                kubectl patch "$app" -n argocd --type json \
                    -p '[{"op":"remove","path":"/metadata/finalizers"}]' 2>/dev/null || true
            done
            sleep 5
            # Delete remaining
            kubectl delete applications --all -n argocd --timeout=30s 2>/dev/null || true
            break
        fi
        echo -n "."
        sleep 5
    done
    echo ""
    log "ArgoCD applications deleted"
else
    log "ArgoCD namespace not found — skipping"
fi

# ─────────────────────────────────────────────────────────────────────
# Step 2: Delete ingresses and load balancers (block VPC deletion)
# ─────────────────────────────────────────────────────────────────────
step "2" "Delete ingresses and load balancers"

if kubectl cluster-info &>/dev/null 2>&1; then
    log "Deleting all ingresses..."
    kubectl delete ingress --all -A --timeout=60s 2>/dev/null || true

    log "Deleting LoadBalancer services..."
    for ns in $(kubectl get namespaces -o name 2>/dev/null); do
        kubectl delete svc -l spec.type=LoadBalancer -n "${ns#namespace/}" 2>/dev/null || true
    done

    log "Waiting for ALBs to be deregistered (30s)..."
    sleep 30

    # Verify no ALBs remain
    ALB_COUNT=$(aws elbv2 describe-load-balancers --region "$REGION" \
        --query "LoadBalancers[?contains(LoadBalancerName, 'kubeauto') || contains(LoadBalancerName, 'k8s-')]" \
        --output json 2>/dev/null | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
    if [[ "$ALB_COUNT" != "0" ]]; then
        warn "$ALB_COUNT ALBs still exist. Waiting 30 more seconds..."
        sleep 30
    fi
else
    log "Cluster not reachable — skipping Kubernetes cleanup"
fi

# ─────────────────────────────────────────────────────────────────────
# Step 3: Uninstall Helm releases
# ─────────────────────────────────────────────────────────────────────
step "3" "Uninstall Helm releases"

if kubectl cluster-info &>/dev/null 2>&1; then
    helm uninstall argocd -n argocd 2>/dev/null || log "ArgoCD already removed"
    helm uninstall aws-load-balancer-controller -n kube-system 2>/dev/null || log "LB Controller already removed"
    log "Helm releases uninstalled"
else
    log "Cluster not reachable — skipping Helm cleanup"
fi

# ─────────────────────────────────────────────────────────────────────
# Step 4: Terraform destroy
# ─────────────────────────────────────────────────────────────────────
step "4" "Terraform destroy (~15 minutes)"

cd "$TF_DIR"

if [[ ! -f terraform.tfstate ]]; then
    warn "No terraform.tfstate found. Nothing to destroy."
else
    log "Running terraform destroy..."
    STEP4_START=$SECONDS
    terraform destroy -auto-approve -input=false
    STEP4_ELAPSED=$((SECONDS - STEP4_START))
    log "Terraform destroy completed in $((STEP4_ELAPSED / 60))m $((STEP4_ELAPSED % 60))s"
fi

# ─────────────────────────────────────────────────────────────────────
# Step 5: Verify cleanup
# ─────────────────────────────────────────────────────────────────────
step "5" "Verify cleanup"

ISSUES=0

# Check EKS cluster
if aws eks describe-cluster --name "$CLUSTER_NAME" --region "$REGION" &>/dev/null; then
    err "EKS cluster still exists!"
    ISSUES=$((ISSUES + 1))
else
    log "EKS cluster: deleted"
fi

# Check NAT gateways
NAT_COUNT=$(aws ec2 describe-nat-gateways --region "$REGION" \
    --filter "Name=tag:Name,Values=*kubeauto*" "Name=state,Values=available" \
    --query 'NatGateways' --output json 2>/dev/null | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" || echo "0")
if [[ "$NAT_COUNT" != "0" ]]; then
    err "$NAT_COUNT NAT gateways still exist!"
    ISSUES=$((ISSUES + 1))
else
    log "NAT gateways: deleted"
fi

# Check running instances
INSTANCE_COUNT=$(aws ec2 describe-instances --region "$REGION" \
    --filters "Name=tag:eks:cluster-name,Values=$CLUSTER_NAME" "Name=instance-state-name,Values=running" \
    --query 'Reservations[*].Instances[*]' --output json 2>/dev/null | python3 -c "import sys,json; print(sum(len(r) for r in json.load(sys.stdin)))" || echo "0")
if [[ "$INSTANCE_COUNT" != "0" ]]; then
    err "$INSTANCE_COUNT EC2 instances still running!"
    ISSUES=$((ISSUES + 1))
else
    log "EC2 instances: none running"
fi

# Check orphaned EBS volumes
EBS_COUNT=$(aws ec2 describe-volumes --region "$REGION" \
    --filters "Name=tag:kubernetes.io/cluster/$CLUSTER_NAME,Values=owned" \
    --query 'Volumes' --output json 2>/dev/null | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" || echo "0")
if [[ "$EBS_COUNT" != "0" ]]; then
    warn "$EBS_COUNT orphaned EBS volumes found (may incur small charges)"
    echo "  To clean up: aws ec2 describe-volumes --region $REGION --filters 'Name=tag:kubernetes.io/cluster/$CLUSTER_NAME,Values=owned'"
    ISSUES=$((ISSUES + 1))
else
    log "EBS volumes: clean"
fi

# Check ALBs
ALB_REMAINING=$(aws elbv2 describe-load-balancers --region "$REGION" \
    --query "length(LoadBalancers[?contains(LoadBalancerName, 'kubeauto') || contains(LoadBalancerName, 'k8s-')])" \
    --output text 2>/dev/null || echo "0")
if [[ "$ALB_REMAINING" != "0" ]]; then
    warn "$ALB_REMAINING ALBs may still exist (check AWS console)"
    ISSUES=$((ISSUES + 1))
else
    log "ALBs: deleted"
fi

# Confirm AWS SM secrets preserved
SM_COUNT=$(aws secretsmanager list-secrets --region "$REGION" \
    --query "length(SecretList[?starts_with(Name, 'kubeauto/')])" \
    --output text 2>/dev/null || echo "0")
log "AWS Secrets Manager: $SM_COUNT kubeauto/ secrets preserved (needed for rebuild)"

# ECR repos
ECR_COUNT=$(aws ecr describe-repositories --region "$REGION" \
    --query "length(repositories[?starts_with(repositoryName, 'kubeauto')])" \
    --output text 2>/dev/null || echo "0")
log "ECR repositories: $ECR_COUNT preserved (needed for rebuild)"

# ─────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────
TOTAL_ELAPSED=$((SECONDS))

echo ""
if [[ $ISSUES -eq 0 ]]; then
    echo -e "${GREEN}╔══════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  TEARDOWN COMPLETE — \$0/hr recurring charges    ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════╝${NC}"
else
    echo -e "${YELLOW}╔══════════════════════════════════════════════════╗${NC}"
    echo -e "${YELLOW}║  TEARDOWN COMPLETE WITH $ISSUES WARNINGS          ║${NC}"
    echo -e "${YELLOW}║  Check items above for potential residual cost   ║${NC}"
    echo -e "${YELLOW}╚══════════════════════════════════════════════════╝${NC}"
fi

echo ""
echo "  Time: $((TOTAL_ELAPSED / 60))m $((TOTAL_ELAPSED % 60))s"
echo ""
echo -e "  ${BLUE}Preserved for rebuild:${NC}"
echo "    AWS Secrets Manager: kubeauto/github-token, kubeauto/github-oauth,"
echo "                         kubeauto/backstage-github-oauth,"
echo "                         kubeauto/argocd-backstage-token, kubeauto/test-secret"
echo "    ECR repositories:    kubeauto-backstage, kubeauto-sample-app, etc."
echo "    GitHub OAuth App:    persists in GitHub settings"
echo "    DNS records:         persist in Namecheap (update CNAME after rebuild)"
echo ""
echo -e "  ${BLUE}To rebuild:${NC}"
echo "    ./scripts/rebuild.sh"
echo "    (all secrets fetched from AWS Secrets Manager automatically)"
