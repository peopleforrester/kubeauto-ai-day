#!/usr/bin/env bash
# ABOUTME: Updates Backstage secrets with runtime-generated K8s and ArgoCD tokens.
# ABOUTME: Run after rebuild.sh or any cluster recreation to refresh service tokens.

set -eo pipefail

REGION="us-west-2"

echo "Generating Backstage K8s SA token..."
K8S_TOKEN=$(kubectl create token backstage -n backstage --duration=8760h)
echo "  K8s token generated (${#K8S_TOKEN} chars)"

echo "Fetching ArgoCD Backstage token from Secrets Manager..."
ARGOCD_TOKEN=$(aws secretsmanager get-secret-value \
    --secret-id kubeauto/argocd-backstage-token \
    --region "$REGION" \
    --query 'SecretString' --output text \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")
echo "  ArgoCD token fetched (${#ARGOCD_TOKEN} chars)"

echo "Creating backstage-secrets in backstage namespace..."
kubectl create secret generic backstage-secrets \
    -n backstage \
    --from-literal="ARGOCD_AUTH_TOKEN=$ARGOCD_TOKEN" \
    --from-literal="K8S_SA_TOKEN=$K8S_TOKEN" \
    --dry-run=client -o yaml | kubectl apply -f -

echo "Restarting Backstage deployment..."
kubectl rollout restart deployment -n backstage -l app.kubernetes.io/name=backstage
kubectl rollout status deployment -n backstage -l app.kubernetes.io/name=backstage --timeout=120s

echo "Done. Backstage tokens updated."
