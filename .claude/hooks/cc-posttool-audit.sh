#!/bin/bash
# ABOUTME: Layer 2 PostToolUse audit hook implementing Guardrails 4, 5, and 6.
# ABOUTME: Deterministic post-execution reminders for verification, audit trail, and rollback.

INPUT=$(cat -)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)

if [ -z "$COMMAND" ]; then
    exit 0
fi

# === Guardrail 5: Immutable Audit Trail ===
# After terraform apply or helm install, remind about scorecard
if echo "$COMMAND" | grep -qE "(terraform apply|helm install|helm upgrade)"; then
    echo "{\"addToConversation\": \"[Guardrail 5: Audit Trail] Component deployed. Update spec/SCORECARD.md with: Toil Reduced (1-10), Correction Cycles, AI Time, Est. Manual Time, Toil Shifted (yes/no), Notes. Then commit with conventional format: phase-X/component: description\"}"
fi

# === Guardrail 4: Assume Misunderstanding ===
# After kubectl apply (in allowed contexts), remind to verify
if echo "$COMMAND" | grep -qE "kubectl\s+apply"; then
    echo "{\"addToConversation\": \"[Guardrail 4: Assume Misunderstanding] Resource applied. Verify with kubectl get and kubectl describe. Check for events, conditions, and readiness. Do not assume success from apply exit code alone.\"}"
fi

# === Guardrail 6: Automated Rollback ===
# After any failed command, suggest rollback options
EXIT_CODE=$(echo "$INPUT" | jq -r '.tool_result.exit_code // 0' 2>/dev/null)
if [ "$EXIT_CODE" != "0" ] && [ "$EXIT_CODE" != "null" ]; then
    if echo "$COMMAND" | grep -q "terraform"; then
        echo "{\"addToConversation\": \"[Guardrail 6: Rollback] Terraform command failed. Consider: terraform plan to check state, git diff to see what changed, git stash or git checkout to revert files.\"}"
    elif echo "$COMMAND" | grep -q "helm"; then
        echo "{\"addToConversation\": \"[Guardrail 6: Rollback] Helm command failed. Consider: helm rollback, helm history to check previous revisions, argocd app sync --revision to force a known-good state.\"}"
    elif echo "$COMMAND" | grep -q "kubectl"; then
        echo "{\"addToConversation\": \"[Guardrail 6: Rollback] kubectl command failed. Check: kubectl describe for events, kubectl logs for container output, argocd app diff for expected state.\"}"
    fi
fi

exit 0
