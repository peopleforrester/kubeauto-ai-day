# AI Platform Building Scorecard — Template

Use this template to measure AI-assisted platform builds honestly.
Fill it in as you go — don't try to reconstruct scores after the fact.

See `methodology.md` for scoring definitions.

## Project Info

- **Project**: _your project name_
- **Date**: _build date_
- **AI Tool**: _tool name and model_
- **Platform**: _target platform (e.g., EKS 1.34, GKE, AKS)_

## Scorecard

| Component | Toil Reduced (1-10) | Correction Cycles | AI Time | Est. Manual Time | Toil Shifted? | Notes |
|---|---|---|---|---|---|---|
| _Component 1_ | | | | | | |
| _Component 2_ | | | | | | |
| _Component 3_ | | | | | | |

## Totals

- Total AI-assisted build time: ___ hours
- Estimated manual build time: ___ hours
- Net toil reduction: ___%
- Total correction cycles: ___
- Average toil reduced score: ___/10
- Components where AI genuinely reduced toil: ___/___
- Components where AI shifted toil (Partial): ___/___
- Components where AI fully shifted toil (Yes): ___/___
- Components where starting from scratch would have been faster: ___/___

## Analysis

### Where AI Helped Most

_List the top 3-5 components where AI provided the most value._

### Where AI Struggled

_List the components where AI required the most correction cycles and why._

### Patterns in Correction Cycles

_What caused most corrections? Stale knowledge? Wrong API versions? Misunderstood requirements?_

### Recommendations

_Based on your experience, what practical advice would you give teams considering AI-assisted platform builds?_

## Scoring Key

**Toil Reduced (1-10):**
- 10 = Would have taken hours manually, AI did it in minutes with no corrections
- 5 = AI produced a starting point, but required significant human correction
- 1 = AI output was wrong enough that starting from scratch would have been faster

**Correction Cycles:** Number of times AI output needed human intervention.

**Toil Shifted?:**
- No = AI genuinely reduced total effort
- Partial = Some reduction, some shift
- Yes = AI converted "writing config" toil into "reviewing and debugging AI config" toil
