# Prompt Recording

This directory captures every prompt used during the AI-assisted IDP build.

## Purpose

The audience sees real prompts, not sanitized ones. Every correction, failure,
and iteration becomes talk material for the KubeAuto Day presentation.

## Recording Format

Each phase file follows this format:

```markdown
## Prompt N (Phase X, HH:MM timestamp)
**Type:** Initial / Correction / Clarification
**Prompt:**
> [exact prompt text]

**Result:** Success / Partial / Failure
**Time spent:** N minutes
**Correction needed:** Yes/No
**Notes:** [what went wrong, what was surprising]
```

## Files

| File | Phase | Status |
|------|-------|--------|
| [phase-01-prompts.md](phase-01-prompts.md) | Foundation | Not started |
| [phase-02-prompts.md](phase-02-prompts.md) | GitOps Bootstrap | Not started |
| [phase-03-prompts.md](phase-03-prompts.md) | Security Stack | Not started |
| [phase-04-prompts.md](phase-04-prompts.md) | Observability | Not started |
| [phase-05-prompts.md](phase-05-prompts.md) | Developer Portal | Not started |
| [phase-06-prompts.md](phase-06-prompts.md) | Integration Testing | Not started |
| [phase-07-prompts.md](phase-07-prompts.md) | Production Hardening | Not started |

## Analysis

After all phases complete, analyze prompt data for:
- Total prompts per phase
- Correction rate (corrections / total prompts)
- Most common correction types
- Phases where AI struggled most
- Time spent on corrections vs productive generation
