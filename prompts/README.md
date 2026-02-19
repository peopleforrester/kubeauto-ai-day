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
| [phase-01-prompts.md](phase-01-prompts.md) | Foundation | Reconstructed |
| [phase-02-prompts.md](phase-02-prompts.md) | GitOps Bootstrap | Reconstructed |
| [phase-03-prompts.md](phase-03-prompts.md) | Security Stack | Reconstructed |
| [phase-04-prompts.md](phase-04-prompts.md) | Observability | Reconstructed |
| [phase-05-prompts.md](phase-05-prompts.md) | Developer Portal | Reconstructed |
| [phase-06-prompts.md](phase-06-prompts.md) | Integration Testing | Reconstructed |
| [phase-07-prompts.md](phase-07-prompts.md) | Production Hardening | Reconstructed |

*Note: Prompt logs were reconstructed from git history (commit timestamps),
scorecard notes (correction cycles), and session transcripts. They capture
the substance of each interaction but are not verbatim transcripts.*

## Analysis

After all phases complete, analyze prompt data for:
- Total prompts per phase
- Correction rate (corrections / total prompts)
- Most common correction types
- Phases where AI struggled most
- Time spent on corrections vs productive generation
