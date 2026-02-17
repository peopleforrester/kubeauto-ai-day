#!/bin/bash
# ABOUTME: Ralph Wiggum stop hook for spec-driven IDP build.
# ABOUTME: Checks for phase completion promise tags; blocks exit if not found.

OUTPUT=$(cat -)

# Check for phase completion promises
if echo "$OUTPUT" | grep -q "<promise>PHASE[0-7]_DONE</promise>"; then
    echo '{"decision": "allow"}'
    exit 0
fi

# Check for explicit stop request
if echo "$OUTPUT" | grep -q "<promise>ALL_PHASES_COMPLETE</promise>"; then
    echo '{"decision": "allow"}'
    exit 0
fi

# Block exit - keep iterating
echo '{"decision": "block", "reason": "Phase completion promise not found. Continue working on current phase. Check test results and fix any failures."}'
exit 0
