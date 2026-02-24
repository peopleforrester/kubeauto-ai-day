#!/bin/bash
# ABOUTME: Layer 2 Stop hook implementing Guardrail 3 (Circuit Breaker).
# ABOUTME: Ralph Wiggum pattern — blocks Claude from exiting without phase completion promise.

OUTPUT=$(cat -)

# Only enforce during active builds — allow exit for non-build tasks
if [ ! -f "$CLAUDE_PROJECT_DIR/.build-active" ]; then
    echo '{"decision": "allow"}'
    exit 0
fi

# Check for phase completion promises
if echo "$OUTPUT" | grep -q "<promise>PHASE[0-7]_DONE</promise>"; then
    echo '{"decision": "allow"}'
    exit 0
fi

# Check for full completion
if echo "$OUTPUT" | grep -q "<promise>ALL_PHASES_COMPLETE</promise>"; then
    echo '{"decision": "allow"}'
    exit 0
fi

# Block exit — keep iterating
echo '{"decision": "block", "reason": "[Guardrail 3: Circuit Breaker] Phase completion promise not found. Continue working on current phase. Run tests, fix failures, update scorecard."}'
exit 0
