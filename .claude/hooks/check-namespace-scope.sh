#!/bin/bash
# ABOUTME: Layer 1 guardrail for blast radius limits (Guardrail 2).
# ABOUTME: Validates manifests only target namespaces allowed for the current phase.

PHASE=$(cat .current-phase 2>/dev/null || echo "0")

# Define which namespaces each phase can touch
case $PHASE in
    1) ALLOWED_NS="default|kube-system|platform|argocd|monitoring|backstage|apps|security" ;;
    2) ALLOWED_NS="argocd|platform|apps|monitoring|backstage|security" ;;
    3) ALLOWED_NS="security|apps|kyverno|falco" ;;
    4) ALLOWED_NS="monitoring|apps" ;;
    5) ALLOWED_NS="backstage|apps" ;;
    6) ALLOWED_NS="apps" ;;
    7) ALLOWED_NS=".*" ;;  # Hardening touches everything
    *) ALLOWED_NS=".*" ;;
esac

VIOLATIONS=0

for file in $(git diff --cached --name-only --diff-filter=ACM 2>/dev/null | grep '\.yaml$'); do
    NS=$(grep -E "^\s+namespace:" "$file" 2>/dev/null | awk '{print $2}' | tr -d "\"'" | head -1)
    if [ -n "$NS" ] && ! echo "$NS" | grep -qE "^($ALLOWED_NS)$"; then
        echo "WARNING: $file targets namespace '$NS' which is outside Phase $PHASE scope"
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
done

if [ $VIOLATIONS -gt 0 ]; then
    echo ""
    echo "Phase $PHASE should only modify namespaces matching: $ALLOWED_NS"
    echo "Override: update .current-phase or modify check-namespace-scope.sh"
    # Warning only — phases sometimes need cross-namespace refs
fi

exit 0
