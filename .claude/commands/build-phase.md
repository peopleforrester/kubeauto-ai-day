# Build Phase $ARGUMENTS

You are building Phase $ARGUMENTS of the KubeAuto Day IDP.

## Instructions

1. Read `spec/BUILD-SPEC.md` for the full build spec
2. Read `spec/phases/phase-0$ARGUMENTS-*.md` for this phase's detailed spec
3. Read `spec/SCORECARD.md` to see current progress
4. Read the relevant `.claude/skills/*.md` files for components in this phase
5. Read the execution plan in `docs/PLAN.md` for Phase $ARGUMENTS steps

## Execution Protocol

For each component in this phase:

1. **Write tests first** in `tests/test_phase_0${ARGUMENTS}_*.py`
   - ABOUTME headers (2-line comment at top)
   - Type hints on all functions
   - No mocks, stubs, or fallbacks
2. **Run tests to confirm they fail** (not import errors)
3. **Implement the component** following the spec
4. **Run tests to confirm they pass**
5. **Update scorecard** (`spec/SCORECARD.md`) for this component
6. **Commit** this component's files to staging branch
   - Verify on staging: `git branch --show-current`
   - Professional commit message, no AI references

## Pre-Push Verification

Before pushing, run the FULL test suite (all phases, not just current):
```bash
git branch --show-current  # Must be "staging"
uv run pytest tests/ -v
git push origin staging
```

## Completion

When ALL tests for Phase $ARGUMENTS pass and scorecard is updated:
- Output `<promise>PHASE${ARGUMENTS}_DONE</promise>`

Do NOT output the promise if any test fails.
If this is Phase 7 and all phases pass: also output `<promise>ALL_PHASES_COMPLETE</promise>`

## Rules Reminder

- Everything after Phase 2 goes through ArgoCD (no kubectl apply)
- No secrets in Git — use External Secrets Operator
- Read skill files BEFORE generating component config
- Record prompts in `prompts/phase-0$ARGUMENTS-prompts.md`
