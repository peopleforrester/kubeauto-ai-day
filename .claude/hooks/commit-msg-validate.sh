#!/bin/bash
# ABOUTME: Layer 1 guardrail for immutable audit trail (Guardrail 5).
# ABOUTME: Enforces conventional commit format with phase/component tags.

MSG_FILE="$1"

if [ -z "$MSG_FILE" ] || [ ! -f "$MSG_FILE" ]; then
    # No message file provided — skip validation
    exit 0
fi

MSG=$(cat "$MSG_FILE")

# Allow merge commits
if echo "$MSG" | grep -qE "^Merge"; then
    exit 0
fi

# Allow fixup and squash commits
if echo "$MSG" | grep -qE "^(fixup|squash)!"; then
    exit 0
fi

# Allow revert commits
if echo "$MSG" | grep -qE "^Revert"; then
    exit 0
fi

# Require phase/component format OR conventional commit format
# phase-X/component: description
# OR: type(scope): description
if echo "$MSG" | grep -qE "^phase-[0-8]/[a-z-]+: .+" || \
   echo "$MSG" | grep -qE "^(feat|fix|docs|style|refactor|test|chore|ci|perf|build)(\([a-z-]+\))?: .+"; then
    exit 0
fi

echo "ERROR: Commit message must follow one of these formats:"
echo "  phase-X/component: description"
echo "  type(scope): description"
echo ""
echo "Examples:"
echo "  phase-3/kyverno: add require-labels policy"
echo "  feat(guardrails): add Layer 1 pre-commit hooks"
echo "  fix(falco): correct write_etc_common macro"
echo ""
echo "Got: $MSG"
exit 1
