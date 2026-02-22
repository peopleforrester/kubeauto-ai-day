#!/bin/bash
# ABOUTME: Layer 1 guardrail for propose-approve-execute and circuit breakers (Guardrails 1, 3).
# ABOUTME: Blocks push if current phase tests don't pass.

PHASE=$(cat .current-phase 2>/dev/null || echo "7")
REPO_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

echo "=== Layer 1 Guardrail: Pre-Push Test Gate ==="
echo "Running Phase $PHASE tests before push..."

cd "$REPO_DIR"

# Run phase-specific tests
if ls tests/test_phase_0${PHASE}_*.py 1>/dev/null 2>&1; then
    uv run pytest "tests/test_phase_0${PHASE}_"*.py -v --timeout=120 2>&1
    TEST_EXIT=$?

    if [ $TEST_EXIT -ne 0 ]; then
        echo ""
        echo "BLOCKED: Phase $PHASE tests are failing. Fix them before pushing."
        echo "Run: uv run pytest tests/test_phase_0${PHASE}_*.py -v"
        exit 1
    fi

    echo "Phase $PHASE tests pass. Push allowed."
else
    echo "No test files found for Phase $PHASE. Skipping test gate."
fi

exit 0
