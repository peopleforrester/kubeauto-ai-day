# KubeAuto Day Europe 2026 — Slide Outline

## Talk Title

**"The 10-Hour IDP: Can Claude Code Actually Reduce Platform Engineering Toil?"**

Speaker: Michael Forrester, Principal Training Architect — KodeKloud

---

## Slide 1: Title

- KubeAuto AI Day Europe 2026
- "The 10-Hour IDP"
- "Can Claude Code Actually Reduce Platform Engineering Toil?"
- Michael Forrester, Principal Training Architect — KodeKloud

## Slide 2: The METR Hook

- Developers believed AI made them +24% faster
- They were actually 19% slower
- 43-point gap between perception and reality
- Source: METR 2025, randomized controlled trial, 16 experienced devs, 246 real tasks

## Slide 3: It Gets Worse

Five data points:
- −1.5% delivery throughput (DORA 2025)
- −7.2% stability (DORA 2025)
- 1% of companies "AI mature" (2025 AI at Work Report)
- 46% of devs don't trust AI output (Stack Overflow 2025)
- 30% of platform teams don't measure (State of Platform Engineering Vol. 4)

## Slide 4: The Question

> Everyone's talking about AI agents in production. I'm not there yet.
> I'm at the beginning — standing up clusters, adding technologies,
> running POCs. The boring part.

- Not "is AI useful?" but "can AI make the boring part disappear?"
- Component by component. With tests. With a timer. With a scorecard.

## Slide 5: The Experiment

- 10 hours total effort
- 27 components across 7 build phases
- 59 tests — all hit real infrastructure, zero mocks
- 6 dimensions per-component scoring
- Claude Code builds. I decide, review, and score.

## Slide 6: What the AI Had to Handle

| Stack | Component | Version |
|-------|-----------|---------|
| Infrastructure | EKS on AWS | 1.34 |
| GitOps | ArgoCD | 3.3.0 |
| Policy | Kyverno | 1.17.0 |
| Runtime Security | Falco (eBPF) | 0.43.0 |
| Secrets | ESO + AWS Secrets Mgr | 1.3.2 |
| Observability | Prometheus + Grafana + OTel | 3.9 / 12.3 / 0.145 |
| Portal | Backstage | 1.9.1 |
| TLS + RBAC | cert-manager + NetworkPolicies + PDBs | 1.19.3 |

27 ArgoCD Applications, app-of-apps pattern, every version pinned in skill files.

## Slide 7: The Scorecard Method

Four steps: Write the test → AI implements → Verify on live infra → Score honestly

6 scoring dimensions:
1. Toil Reduced (1–10)
2. Correction Cycles (count)
3. AI Time (minutes)
4. Manual Time (minutes)
5. Toil Shifted? (yes/no)
6. Notes (honest)

"The scorecard is the artifact. Not the platform."

## Slide 8: Live Demo — GitOps in Action

- 27 synced apps, drift detection, 30-second self-heal
- LIVE DEMO

## Slide 9: Live Demo — Security Stack

- Kyverno blocks bad pods, Falco catches runtime threats, ESO syncs secrets
- LIVE DEMO

## Slide 10: Live Demo — Developer Portal

- Backstage catalog, deploy-service template, Kyverno-compliant output
- LIVE DEMO

## Slide 11: METR vs This Experiment

| | METR Study (2025) | This Experiment (2026) |
|---|---|---|
| Result | Believed +20%, actual −19% | Measured 73.8% toil reduction |
| Build time | — | 3:10 AI vs 12:05 manual |
| Method | Self-reported time | TDD + per-component scorecard |
| Constraints | None | Skill files + pinned versions + TDD + guardrails |
| AI usage | Autocomplete | Constrained agent |

"The difference isn't the AI. It's the constraints."

## Slide 12: Correction Cycle Distribution

- 0 corrections: 11 components (41%)
- 1 correction: 10 components (37%)
- 2 corrections: 3 components (11%)
- 3 corrections: 3 components (11%)

78% worked in 0–1 cycles. The 3-cycle outliers tell the real story.

## Slide 13: Same Root Cause. Every Time.

| Component | Cycles | Root Cause |
|-----------|--------|------------|
| EKS Cluster | 3 | Terraform module v21 renamed variables. AI used old names. |
| Kyverno | 3 | Webhook config changed between chart versions. CRDs too large for client-side apply. |
| OTel Collector | 3 | Chart 0.145 requires explicit image.repository. Wrong image variant. |
| ESO | 2 | API version v1 not v1beta1. ArgoCD cache stale after fix. |

"Version currency. Syntactically correct YAML for the wrong version of the software."

## Slide 14: The Four Constraints

> AI didn't make me 19% slower. AI made me 73.8% faster.

1. **Skill files** — pinned versions, known pitfalls, correct API shapes
2. **TDD** — failing test first = immediate signal when AI is wrong
3. **Guardrails** — three layers preventing AI from touching what it shouldn't
4. **Human review** — every output scored, every correction documented

"AI is phenomenal at boring. Infrastructure should be boring. That's the point."

## Slide 15: What 73.8% Doesn't Tell You

Three honest caveats:
- **60+ hours** of invisible investment came first (skill files, hooks, state
  persistence, CLAUDE.md, CI/CD, studying context windows)
- **30 years** of experience caught the errors (module v20 vs v21 in seconds;
  a junior might not catch it for days)
- **1 data point** against their sixteen (rigorous per-component, but tiny
  sample size — evidence, not proof)

"Every impressive number has a denominator. Now you know mine."

## Slide 16: Three-Layer Guardrails

```
Layer 1: Git Hooks
  Determinism: 100%    Latency: <1s    Bypass: None
  gitleaks · yamllint · kubeconform · terraform · helm · trivy ·
  image-allowlist · namespace-scope

Layer 2: Claude Code Hooks
  Determinism: ~80%    Latency: 1-30s    Bypass: Low
  PreToolUse blocks · PostToolUse audit · Stop hook · SessionStart context

Layer 3: Kubernetes
  Determinism: 100%    Latency: 1-5s    Bypass: None
  Kyverno admission · Falco runtime · RBAC · NetworkPolicy ·
  ResourceQuota · ArgoCD GitOps
```

"Catch problems at the cheapest possible point."

## Slide 17: The Eight Guardrails

| # | Guardrail | Implementation |
|---|-----------|----------------|
| 1 | Propose-Approve-Execute | ArgoCD GitOps |
| 2 | Blast Radius Limits | RBAC + Quotas + NetworkPolicies |
| 3 | Stop Hooks & Circuit Breakers | Kyverno + Falco |
| 4 | Assume Misunderstanding | Schema validation + TDD |
| 5 | Immutable Audit Trail | OTel + K8s audit + git log |
| 6 | Automated Rollback | ArgoCD self-heal (<30s) |
| 7 | Secrets & Credential Isolation | ESO + Pod Identity |
| 8 | Supply Chain Validation | Kyverno image registry allowlist |

**NOTE:** Slide currently says "Sigstore" for #8 but only image registry
allowlisting is implemented. Either fix slide to say "image registry
allowlist" or implement cosign verification before the talk.

## Slide 18: Honest Boundaries

Three conditions that made this work:
1. **Greenfield** — no existing tribal knowledge, no org decisions baked in
2. **I understand every component** — could review every line AI generated
3. **Constrained agent, not autocomplete** — skill files, pinned versions,
   TDD, guardrails. Remove any of these and the 73.8% collapses.

## Slide 19: The Platform Is a Demo. The Scorecard Is the Evidence.

> The industry has a measurement problem. We have vendor surveys that say
> +55%. We have METR saying −19%. We have developers who believe +20%
> while being −19%.

"We need more data points. Not more demos."

## Slide 20: Your Turn

- `github.com/peopleforrester/kubeauto-ai-day`
- Full platform code, 59 tests, 27 scored components
- QR code
- Steps: Copy scorecard template → Read methodology → Build your own, score it, share
- `scorecard/SCORECARD-TEMPLATE.md`
- `scorecard/methodology.md`
- "Cluster is live until tomorrow. Go break things."

## Slide 21: Q&A / Contact

- Michael Forrester, Principal Training Architect — KodeKloud
- "Teaching 100,000+ engineers how to build this stuff."
- `github.com/peopleforrester/kubeauto-ai-day`
- `github.com/peopleforrester`
- `youtube.com/@KodeKloud24`

---

## Errata to Fix in Slides

These items were found during validation against repo data:

1. **Slide 11**: "12:08 manual" should be **12:05** (SCORECARD.md says 725 min = 12h 5m)
2. **Slide 12**: Correction breakdown is wrong. Actual counts from scorecard rows:
   - 0 corrections: **11** components (41%) — slide says 13 (48%)
   - 1 correction: **10** components (37%) — slide says 9 (33%)
   - 2 corrections: 3 (11%) — correct
   - 3 corrections: 3 (11%) — correct
   - Also update the "81% worked in 0–1 cycles" line to **78%** (21/27)
3. **Slide 17**: Guardrail #8 says "Sigstore" but only Kyverno image registry
   allowlisting is deployed. Change to "Kyverno image registry allowlist"
   unless cosign verification is added before the talk.

## Notes for Speaker

- Total talk time: ~27 min target for 30-minute slot
- 21 slides (was 19 in original outline)
- Demo buffer: have screenshots as fallback if live demo fails
- Key talking points:
  - This is about measurement, not advocacy
  - The scorecard template is the takeaway
  - "Toil shifted" is the nuanced finding
  - Version currency is AI's biggest weakness
  - The caveats slide (#15) builds trust — don't skip it
  - The METR comparison (#11) is the argumentative core
