# Validate Phase $ARGUMENTS

Run the test suite for Phase $ARGUMENTS and report results.

## Instructions

1. Run the phase-specific tests:
```bash
uv run pytest tests/test_phase_0${ARGUMENTS}_*.py -v --timeout=120
```

2. Report the results:
   - Total tests: X
   - Passed: X
   - Failed: X
   - Errors: X

3. For each failure, provide:
   - Test name
   - Error message
   - Likely root cause
   - Suggested fix

4. Run the FULL test suite to check for regressions:
```bash
uv run pytest tests/ -v --timeout=120
```

5. Report any regressions in prior phase tests

## Gate Check

Compare results against the phase gate criteria in `spec/BUILD-SPEC.md`.
List each gate item and whether it passes or fails.

If all gate items pass, output: `Phase $ARGUMENTS gate: PASS`
If any gate item fails, output: `Phase $ARGUMENTS gate: FAIL` with details.
