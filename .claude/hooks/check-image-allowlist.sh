#!/bin/bash
# ABOUTME: Layer 1 guardrail for supply chain validation (Guardrail 8).
# ABOUTME: Blocks images from unauthorized registries in Kubernetes manifests.

ALLOWED_REGISTRIES=(
    "public.ecr.aws"
    "quay.io"
    "ghcr.io"
    "registry.k8s.io"
    "docker.io/library"
    "docker.io/grafana"
    "docker.io/falcosecurity"
    "docker.io/otel"
    "docker.io/prom"
    "docker.io/bitnami"
    "docker.io/curlimages"
    "docker.io/busybox"
    "docker.io/nginx"
    "docker.io/python"
    "docker.io/backstage"
    "gcr.io"
    "nvcr.io"
    # ECR registries matching account pattern
    ".dkr.ecr."
)

VIOLATIONS=0

for file in $(find gitops/apps security/ policies/ sample-app/k8s/ backstage/ monitoring/ -name "*.yaml" 2>/dev/null); do
    IMAGES=$(grep -E "^\s+image:" "$file" 2>/dev/null | awk '{print $2}' | tr -d "\"'" )
    for img in $IMAGES; do
        [ -z "$img" ] && continue
        ALLOWED=false

        # Allow images without a registry prefix (defaults to docker.io/library)
        if ! echo "$img" | grep -q "/"; then
            continue
        fi

        for reg in "${ALLOWED_REGISTRIES[@]}"; do
            if echo "$img" | grep -q "$reg"; then
                ALLOWED=true
                break
            fi
        done

        if [ "$ALLOWED" = false ]; then
            echo "BLOCKED: Unauthorized image registry: $img in $file"
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    done
done

if [ $VIOLATIONS -gt 0 ]; then
    echo ""
    echo "Add approved registries to .claude/hooks/check-image-allowlist.sh"
    exit 1
fi

exit 0
