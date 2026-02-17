#!/bin/bash
# ABOUTME: Overnight batch build script for Ralph Wiggum loop execution.
# ABOUTME: Runs all 7 phases sequentially, gating each on test success.

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$REPO_DIR/recordings/logs"
mkdir -p "$LOG_DIR"

PHASES=(1 2 3 4 5 6 7)
MAX_ITERS=(15 20 30 20 20 15 15)

echo "========================================="
echo "KubeAuto Day IDP - Overnight Build"
echo "Started: $(date)"
echo "========================================="
echo ""

for i in "${!PHASES[@]}"; do
    PHASE=${PHASES[$i]}
    ITERS=${MAX_ITERS[$i]}

    echo "========================================="
    echo "Starting Phase $PHASE (max $ITERS iterations)"
    echo "$(date)"
    echo "========================================="

    cd "$REPO_DIR"
    claude -p "/build-phase $PHASE" \
        --max-iterations "$ITERS" \
        2>&1 | tee "$LOG_DIR/phase-${PHASE}.log"

    # Verify phase tests pass before continuing
    echo ""
    echo "Running Phase $PHASE tests..."
    uv run pytest "tests/test_phase_0${PHASE}_"*.py -v 2>&1 | tee -a "$LOG_DIR/phase-${PHASE}.log"

    if [ $? -ne 0 ]; then
        echo ""
        echo "PHASE $PHASE TESTS FAILED. Stopping build."
        echo "Failed at: $(date)"
        exit 1
    fi

    echo ""
    echo "Phase $PHASE complete. Moving to next phase."
    echo ""
done

echo "========================================="
echo "ALL PHASES COMPLETE"
echo "Finished: $(date)"
echo "========================================="
