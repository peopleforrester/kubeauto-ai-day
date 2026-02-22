#!/bin/bash
# ABOUTME: Layer 2 PreToolUse guard implementing Guardrails 1, 2, and 7.
# ABOUTME: Deterministic blocks on dangerous kubectl, terraform, and secret-exposure commands.

INPUT=$(cat -)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)

if [ -z "$COMMAND" ]; then
    exit 0
fi

# === Guardrail 1: Propose-Approve-Execute ===
# After Phase 2, block kubectl apply in production namespaces
if [ -f "$CLAUDE_PROJECT_DIR/gitops/bootstrap/app-of-apps.yaml" ]; then
    BLOCKED_NS="platform|argocd|monitoring|backstage|apps|security"
    if echo "$COMMAND" | grep -qE "kubectl\s+(apply|create|replace).*-n\s+($BLOCKED_NS)"; then
        echo "{\"decision\": \"block\", \"reason\": \"[Guardrail 1: Propose-Approve-Execute] After Phase 2, all resources must be deployed via ArgoCD GitOps. Write manifests to gitops/apps/ and let ArgoCD sync them.\"}" >&2
        exit 2
    fi
fi

# === Guardrail 2: Blast Radius Limits ===
# Never allow write operations on kube-system
if echo "$COMMAND" | grep -qE "kubectl\s+(delete|apply|patch|edit).*-n\s+kube-system"; then
    echo "{\"decision\": \"block\", \"reason\": \"[Guardrail 2: Blast Radius Limits] Write operations on kube-system are blocked. Only read operations (get, describe, logs) are allowed.\"}" >&2
    exit 2
fi

# Block terraform destroy without explicit flag
if echo "$COMMAND" | grep -qE "terraform\s+destroy" && ! echo "$COMMAND" | grep -q "CONFIRMED_DESTROY=true"; then
    echo "{\"decision\": \"block\", \"reason\": \"[Guardrail 2: Blast Radius Limits] terraform destroy requires CONFIRMED_DESTROY=true environment variable. This prevents accidental infrastructure deletion.\"}" >&2
    exit 2
fi

# Block kubectl delete namespace
if echo "$COMMAND" | grep -qE "kubectl\s+delete\s+namespace"; then
    echo "{\"decision\": \"block\", \"reason\": \"[Guardrail 2: Blast Radius Limits] Namespace deletion is blocked. Remove via Terraform or ArgoCD only.\"}" >&2
    exit 2
fi

# === Guardrail 7: Secrets & Credential Isolation ===
# Block commands that would expose secrets in logs
if echo "$COMMAND" | grep -qE "kubectl\s+get\s+secret.*-o\s+(yaml|json)"; then
    echo "{\"decision\": \"block\", \"reason\": \"[Guardrail 7: Secrets Isolation] Do not dump full secrets. Use: kubectl get secret <name> -o jsonpath='{.data.<key>}' for specific fields only.\"}" >&2
    exit 2
fi

# Block cat/echo of common secret file patterns
if echo "$COMMAND" | grep -qE "(cat|echo|less|more)\s+.*(\.pem|\.key|\.crt|credentials|\.env\b|tfstate)"; then
    echo "{\"decision\": \"block\", \"reason\": \"[Guardrail 7: Secrets Isolation] Reading secret/credential files directly is blocked. Use External Secrets Operator or AWS Secrets Manager CLI.\"}" >&2
    exit 2
fi

exit 0
