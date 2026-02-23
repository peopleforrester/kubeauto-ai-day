#!/usr/bin/env bash
# ABOUTME: Automated rebuild script for the KubeAuto Day IDP platform.
# ABOUTME: Takes the platform from zero to fully running in ~45 minutes.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TF_DIR="$REPO_ROOT/infrastructure/terraform"
REGION="us-west-2"
CLUSTER_NAME="kubeauto-ai-day"
ARGOCD_NAMESPACE="argocd"
ARGOCD_CHART_VERSION="9.4.2"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()  { echo -e "${GREEN}[$(date +%H:%M:%S)]${NC} $*"; }
warn() { echo -e "${YELLOW}[$(date +%H:%M:%S)] WARNING:${NC} $*"; }
err()  { echo -e "${RED}[$(date +%H:%M:%S)] ERROR:${NC} $*" >&2; }
step() { echo -e "\n${BLUE}═══════════════════════════════════════════${NC}"; echo -e "${BLUE}  STEP $1: $2${NC}"; echo -e "${BLUE}═══════════════════════════════════════════${NC}\n"; }

SECONDS=0
TOTAL_START=$SECONDS

# ─────────────────────────────────────────────────────────────────────
# Pre-flight checks
# ─────────────────────────────────────────────────────────────────────
step "0" "Pre-flight checks"

MISSING=""
for cmd in aws terraform kubectl helm; do
    if ! command -v "$cmd" &>/dev/null; then
        MISSING="$MISSING $cmd"
    fi
done
if [[ -n "$MISSING" ]]; then
    err "Missing required tools:$MISSING"
    exit 1
fi
log "All required tools found"

# Verify AWS credentials
if ! aws sts get-caller-identity &>/dev/null; then
    err "AWS credentials not configured. Run 'aws configure' or set AWS_PROFILE."
    exit 1
fi
ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
log "AWS account: $ACCOUNT_ID"

# Get GitHub token — try AWS Secrets Manager first, fall back to env var
if [[ -z "${GITHUB_TOKEN:-}" ]]; then
    log "GITHUB_TOKEN not set, fetching from AWS Secrets Manager..."
    GH_TOKEN_JSON=$(aws secretsmanager get-secret-value \
        --secret-id kubeauto/github-token \
        --region "$REGION" \
        --query 'SecretString' --output text 2>/dev/null) || true
    if [[ -n "$GH_TOKEN_JSON" ]]; then
        GITHUB_TOKEN=$(echo "$GH_TOKEN_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
        export GITHUB_TOKEN
        log "GitHub token loaded from AWS Secrets Manager"
    else
        err "GITHUB_TOKEN not set and kubeauto/github-token not found in Secrets Manager."
        echo "  Either: export GITHUB_TOKEN=ghp_your_token_here"
        echo "  Or:     aws secretsmanager create-secret --name kubeauto/github-token --secret-string '{\"token\":\"ghp_...\"}' --region $REGION"
        exit 1
    fi
else
    log "GITHUB_TOKEN set via environment"
fi

# Check for Terraform state from previous run
if [[ -f "$TF_DIR/terraform.tfstate" ]]; then
    warn "Existing terraform.tfstate found. This script expects a clean start."
    echo "  If the cluster already exists, this script will update it in-place."
    echo "  Press Enter to continue or Ctrl+C to abort..."
    read -r
fi

# ─────────────────────────────────────────────────────────────────────
# Step 1: Terraform — EKS, VPC, IAM, LB Controller (~20 min)
# ─────────────────────────────────────────────────────────────────────
step "1" "Terraform apply — EKS cluster, VPC, IAM, LB Controller (~20 min)"

cd "$TF_DIR"

log "Running terraform init..."
terraform init -input=false

log "Running terraform plan..."
terraform plan -out=plan.out -input=false

log "Running terraform apply (this takes ~20 minutes)..."
STEP1_START=$SECONDS
terraform apply -input=false plan.out
STEP1_ELAPSED=$((SECONDS - STEP1_START))
log "Terraform apply completed in $((STEP1_ELAPSED / 60))m $((STEP1_ELAPSED % 60))s"

# ─────────────────────────────────────────────────────────────────────
# Step 2: Configure kubectl
# ─────────────────────────────────────────────────────────────────────
step "2" "Configure kubectl"

aws eks update-kubeconfig --name "$CLUSTER_NAME" --region "$REGION"
log "kubeconfig updated"

log "Waiting for nodes to be Ready..."
RETRIES=0
until kubectl get nodes -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null | grep -q "True"; do
    RETRIES=$((RETRIES + 1))
    if [[ $RETRIES -gt 60 ]]; then
        err "Nodes not ready after 5 minutes"
        kubectl get nodes
        exit 1
    fi
    echo -n "."
    sleep 5
done
echo ""
log "Nodes are Ready:"
kubectl get nodes

# ─────────────────────────────────────────────────────────────────────
# Step 3: Install ArgoCD via Helm
# ─────────────────────────────────────────────────────────────────────
step "3" "Install ArgoCD via Helm"

helm repo add argo https://argoproj.github.io/argo-helm 2>/dev/null || true
helm repo update argo

log "Installing ArgoCD (chart $ARGOCD_CHART_VERSION)..."
kubectl create namespace "$ARGOCD_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install argocd argo/argo-cd \
    --namespace "$ARGOCD_NAMESPACE" \
    --version "$ARGOCD_CHART_VERSION" \
    --values "$REPO_ROOT/gitops/argocd/values.yaml" \
    --wait --timeout 5m

log "ArgoCD installed"
kubectl get pods -n "$ARGOCD_NAMESPACE"

# ─────────────────────────────────────────────────────────────────────
# Step 4: Create ArgoCD repo secret (private repo access)
# ─────────────────────────────────────────────────────────────────────
step "4" "Create ArgoCD repo secret"

kubectl apply -f - <<REPOSECRET
apiVersion: v1
kind: Secret
metadata:
  name: repo-kubeauto
  namespace: $ARGOCD_NAMESPACE
  labels:
    argocd.argoproj.io/secret-type: repository
type: Opaque
stringData:
  url: https://github.com/peopleforrester/kubeauto-ai-day.git
  username: git
  password: "$GITHUB_TOKEN"
  type: git
REPOSECRET
log "Repo secret created"

# ─────────────────────────────────────────────────────────────────────
# Step 5: Patch ArgoCD secret with Dex GitHub OAuth credentials
# ─────────────────────────────────────────────────────────────────────
step "5" "Configure Dex GitHub OAuth for ArgoCD"

log "Fetching GitHub OAuth credentials from AWS Secrets Manager..."
GITHUB_OAUTH_JSON=$(aws secretsmanager get-secret-value \
    --secret-id kubeauto/github-oauth \
    --region "$REGION" \
    --query 'SecretString' --output text 2>/dev/null) || true

if [[ -n "$GITHUB_OAUTH_JSON" ]]; then
    DEX_CLIENT_ID=$(echo "$GITHUB_OAUTH_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['clientID'])")
    DEX_CLIENT_SECRET=$(echo "$GITHUB_OAUTH_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['clientSecret'])")

    kubectl patch secret argocd-secret -n "$ARGOCD_NAMESPACE" \
        --type merge -p "{\"stringData\":{\"dex.github.clientID\":\"$DEX_CLIENT_ID\",\"dex.github.clientSecret\":\"$DEX_CLIENT_SECRET\"}}"
    log "Dex GitHub OAuth credentials patched"
else
    warn "kubeauto/github-oauth not found in Secrets Manager"
    warn "ArgoCD will work but GitHub OIDC login will be unavailable"
    warn "To fix later: aws secretsmanager create-secret --name kubeauto/github-oauth ..."
fi

# ─────────────────────────────────────────────────────────────────────
# Step 6: Create Backstage secrets
# ─────────────────────────────────────────────────────────────────────
step "6" "Create Backstage secrets"

# Create backstage namespace
kubectl create namespace backstage --dry-run=client -o yaml | kubectl apply -f -

# Backstage GitHub OAuth
log "Fetching Backstage GitHub OAuth from AWS Secrets Manager..."
BS_OAUTH_JSON=$(aws secretsmanager get-secret-value \
    --secret-id kubeauto/backstage-github-oauth \
    --region "$REGION" \
    --query 'SecretString' --output text 2>/dev/null) || true

if [[ -n "$BS_OAUTH_JSON" ]]; then
    BS_CLIENT_ID=$(echo "$BS_OAUTH_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['clientID'])")
    BS_CLIENT_SECRET=$(echo "$BS_OAUTH_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['clientSecret'])")

    kubectl apply -f - <<BSOAUTH
apiVersion: v1
kind: Secret
metadata:
  name: backstage-github-oauth
  namespace: backstage
type: Opaque
stringData:
  clientID: "$BS_CLIENT_ID"
  clientSecret: "$BS_CLIENT_SECRET"
BSOAUTH
    log "Backstage GitHub OAuth secret created"
else
    warn "kubeauto/backstage-github-oauth not found — Backstage GitHub login will be unavailable"
fi

# ArgoCD Backstage token
log "Fetching ArgoCD Backstage token from AWS Secrets Manager..."
ARGOCD_TOKEN_JSON=$(aws secretsmanager get-secret-value \
    --secret-id kubeauto/argocd-backstage-token \
    --region "$REGION" \
    --query 'SecretString' --output text 2>/dev/null) || true

if [[ -n "$ARGOCD_TOKEN_JSON" ]]; then
    ARGOCD_TOKEN=$(echo "$ARGOCD_TOKEN_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

    # Generate a K8s SA token for Backstage
    K8S_TOKEN=$(kubectl create token backstage-reader -n backstage --duration=8760h 2>/dev/null || echo "")

    if [[ -z "$K8S_TOKEN" ]]; then
        warn "backstage-reader SA doesn't exist yet (will be created by ArgoCD). Token will need manual creation later."
        K8S_TOKEN="placeholder-will-update-after-argocd-sync"
    fi

    kubectl apply -f - <<BSSECRETS
apiVersion: v1
kind: Secret
metadata:
  name: backstage-secrets
  namespace: backstage
type: Opaque
stringData:
  ARGOCD_AUTH_TOKEN: "$ARGOCD_TOKEN"
  K8S_SA_TOKEN: "$K8S_TOKEN"
BSSECRETS
    log "Backstage secrets created"
else
    warn "kubeauto/argocd-backstage-token not found — Backstage ArgoCD plugin will be unavailable"
fi

# ─────────────────────────────────────────────────────────────────────
# Step 7: Apply app-of-apps (bootstraps all 27 applications)
# ─────────────────────────────────────────────────────────────────────
step "7" "Apply app-of-apps (bootstraps all 27 ArgoCD applications)"

kubectl apply -f "$REPO_ROOT/gitops/bootstrap/app-of-apps.yaml"
log "App-of-apps applied. ArgoCD will now sync all applications."
log "This takes ~15-20 minutes for all 27 apps to become Healthy."

# ─────────────────────────────────────────────────────────────────────
# Step 8: Wait for applications to sync
# ─────────────────────────────────────────────────────────────────────
step "8" "Waiting for ArgoCD applications to sync"

WAIT_START=$SECONDS
MAX_WAIT=1200  # 20 minutes

while true; do
    ELAPSED=$((SECONDS - WAIT_START))
    if [[ $ELAPSED -gt $MAX_WAIT ]]; then
        warn "Timeout after 20 minutes. Some apps may still be syncing."
        break
    fi

    TOTAL=$(kubectl get applications -n "$ARGOCD_NAMESPACE" --no-headers 2>/dev/null | wc -l)
    HEALTHY=$(kubectl get applications -n "$ARGOCD_NAMESPACE" --no-headers 2>/dev/null | grep -c "Healthy" || true)
    SYNCED=$(kubectl get applications -n "$ARGOCD_NAMESPACE" --no-headers 2>/dev/null | grep -c "Synced" || true)
    DEGRADED=$(kubectl get applications -n "$ARGOCD_NAMESPACE" --no-headers 2>/dev/null | grep -c "Degraded" || true)

    echo -ne "\r  [${ELAPSED}s] Apps: $TOTAL total, $HEALTHY healthy, $SYNCED synced, $DEGRADED degraded   "

    if [[ $TOTAL -gt 20 && $HEALTHY -ge $((TOTAL - 2)) ]]; then
        echo ""
        log "Most applications are healthy ($HEALTHY/$TOTAL)"
        break
    fi

    sleep 10
done

echo ""
log "Application status:"
kubectl get applications -n "$ARGOCD_NAMESPACE" --sort-by='{.metadata.name}' 2>/dev/null | head -35

# ─────────────────────────────────────────────────────────────────────
# Step 9: Fix Backstage K8s token (now that SA exists)
# ─────────────────────────────────────────────────────────────────────
step "9" "Update Backstage K8s token (post-sync)"

if kubectl get sa backstage-reader -n backstage &>/dev/null; then
    K8S_TOKEN=$(kubectl create token backstage-reader -n backstage --duration=8760h 2>/dev/null || echo "")
    if [[ -n "$K8S_TOKEN" && -n "${ARGOCD_TOKEN:-}" ]]; then
        kubectl apply -f - <<BSUPDATE
apiVersion: v1
kind: Secret
metadata:
  name: backstage-secrets
  namespace: backstage
type: Opaque
stringData:
  ARGOCD_AUTH_TOKEN: "$ARGOCD_TOKEN"
  K8S_SA_TOKEN: "$K8S_TOKEN"
BSUPDATE
        log "Backstage K8s token updated with real SA token"
        # Restart Backstage to pick up the new token
        kubectl rollout restart deployment -n backstage -l app.kubernetes.io/name=backstage 2>/dev/null || true
    fi
else
    warn "backstage-reader SA not found. Backstage K8s plugin may not work."
fi

# ─────────────────────────────────────────────────────────────────────
# Step 10: Post-rebuild summary
# ─────────────────────────────────────────────────────────────────────
step "10" "Post-rebuild summary"

TOTAL_ELAPSED=$((SECONDS - TOTAL_START))

echo ""
log "Platform rebuild complete in $((TOTAL_ELAPSED / 60))m $((TOTAL_ELAPSED % 60))s"
echo ""

# Get ALB hostname
ALB_HOST=$(kubectl get ingress -n argocd -o jsonpath='{.items[0].status.loadBalancer.ingress[0].hostname}' 2>/dev/null || echo "pending")
echo -e "${BLUE}Platform URLs:${NC}"
echo "  ArgoCD:     https://test1.ai-enhanced-devops.com"
echo "  Backstage:  https://backstage.ai-enhanced-devops.com"
echo ""
echo -e "${BLUE}ALB Hostname:${NC}"
echo "  $ALB_HOST"
echo ""
echo -e "${YELLOW}MANUAL STEPS REQUIRED:${NC}"
echo "  1. Update DNS CNAME in Namecheap:"
echo "     *.ai-enhanced-devops.com → $ALB_HOST"
echo ""
echo "  2. Verify applications:"
echo "     kubectl get applications -n argocd"
echo ""
echo "  3. Run the test suite:"
echo "     uv run pytest tests/ -v"
echo ""
echo -e "${BLUE}Note:${NC} GitHub OAuth callback URLs use the domain name, not the ALB"
echo "  hostname, so they should still work without changes."
echo ""
echo -e "${GREEN}Done!${NC}"
