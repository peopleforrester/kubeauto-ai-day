# AI Platform Building Scorecard — Methodology

## Purpose

This scorecard measures whether AI-assisted platform building genuinely reduces
toil or merely shifts it from "writing YAML" to "reviewing and debugging AI YAML."

The goal is honest measurement, not advocacy. If AI made something harder, we say so.

## Scoring Dimensions

Each of the 27 planned components is scored across six dimensions:

### 1. Toil Reduced (1–10)

How much effort did AI save compared to writing the component by hand?

| Score | Meaning |
|-------|---------|
| 10 | Would have taken hours manually; AI did it in minutes with zero corrections |
| 7–9 | AI produced correct or near-correct output; minor adjustments only |
| 4–6 | AI produced a starting point, but required significant human intervention |
| 1–3 | AI output was wrong enough that starting from scratch would have been faster |

### 2. Correction Cycles

The number of times AI output required human intervention before the component
passed its tests. A correction cycle includes:

- Fixing a wrong Helm value or API version
- Correcting a dependency or ordering issue
- Rewriting a section the AI got fundamentally wrong
- Debugging an issue caused by stale AI knowledge (outdated chart versions, removed APIs)

A correction cycle does NOT include:
- Normal iteration during TDD (write test → implement → test → refine)
- Human decisions about architecture or design

### 3. AI Time

Wall-clock time from "start implementing this component" to "tests pass."
This includes all correction cycles. Measured from git log timestamps and
session recordings.

### 4. Estimated Manual Time

How long would this component take an experienced platform engineer building
from scratch without AI assistance? Based on the author's professional
experience building similar platforms. Intentionally conservative (generous to AI).

### 5. Toil Shifted?

Did AI genuinely reduce total effort, or did it convert one type of toil
(writing config) into another type (debugging AI config)?

| Value | Meaning |
|-------|---------|
| No | AI genuinely reduced total effort |
| Partial | Some reduction, but notable debugging overhead from AI errors |
| Yes | AI converted "writing YAML" toil into "reviewing and debugging AI YAML" toil |

### 6. Notes

Free-text field capturing what specifically went right or wrong. These notes
are the most valuable part of the scorecard — they tell the story that numbers
alone cannot.

## Methodology

### Build Protocol

1. **Test-Driven Development**: Every component starts with a failing test.
   The test must fail before implementation begins (no vacuous passes).

2. **Real Infrastructure Only**: All tests run against a live EKS cluster.
   No mocked Kubernetes clients, no stubbed AWS calls. If the cluster is
   unavailable, the test fails — that's correct behavior.

3. **AI Skill Files**: Claude Code was given `.claude/skills/` files with
   component-specific patterns (Helm values, API versions, common pitfalls).
   These represent "good prompting" — giving AI the context it needs.

4. **Per-Component Commits**: Each component is committed separately after
   its tests pass, providing clean git history for analysis.

5. **Honest Recording**: Correction cycles and issues are recorded as they
   happen, not reconstructed after the fact. The scorecard is updated
   alongside each component commit.

### What Counts as "AI-Assisted"

The AI (Claude Code with Opus model) performed:
- Generating Terraform, Helm values, Kubernetes manifests
- Writing Python test files
- Creating ArgoCD Application manifests
- Drafting documentation (ADRs, SECURITY.md, etc.)
- Debugging deployment issues via kubectl/ArgoCD inspection

The human (Michael) performed:
- Architecture decisions (captured in ADRs)
- Approving or rejecting AI suggestions
- Manual AWS console operations (Secrets Manager, IAM verification)
- Directing the build sequence and priorities
- Providing correction when AI output was wrong

### Limitations

- **Estimated manual time is subjective.** Different engineers would produce
  different estimates. We erred on the conservative side (generous to AI).

- **AI time includes thinking time.** When the AI paused to read docs or
  explore the codebase, that counts as AI time even though a human might
  have done it faster.

- **Single data point.** This is one build by one team with one AI tool.
  Results may not generalize to other platforms, tools, or teams.

- **Skill files bias results upward.** The `.claude/skills/` files were
  written with knowledge of common pitfalls. Without them, correction
  cycles would likely be higher.

## Worked Example

**Component: OTel Collector Config** (from the KubeAuto Day build)

| Dimension | Value | Rationale |
|-----------|-------|-----------|
| Toil Reduced | 6/10 | AI produced a working config but required 3 rounds of correction |
| Correction Cycles | 3 | (1) Chart 0.145.0 breaking change for image.repository, (2) wrong image variant (k8s lacks prometheusremotewrite), (3) DaemonSet mode disables Service by default |
| AI Time | 15 min | Including all 3 correction rounds |
| Est. Manual Time | 35 min | Reading chart changelog + values reference + testing |
| Toil Shifted? | Partial | AI saved time on initial YAML but debugging version-specific quirks took extra effort |
| Notes | Root cause of all 3 corrections: stale AI knowledge about chart breaking changes |

**Key insight:** The 3 correction cycles all stemmed from a single root cause —
the AI's training data did not include the 0.145.0 breaking changes. A skill file
with current chart notes would have prevented all three.

## How to Use the Scorecard Template

See `SCORECARD-TEMPLATE.md` for a blank template you can use for your own
AI-assisted builds. Fill it in as you go — don't try to reconstruct scores
after the fact.
