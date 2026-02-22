# KubeAuto Day Europe 2026 — Slide Outline

## Talk Title

**"I Built an IDP with AI. Here's the Scorecard."**

Subtitle: Honest Measurement of AI-Assisted Platform Engineering

Speaker: Michael Forrester, KodeKloud

---

## Slide 1: Title

- Talk title
- Speaker name + role
- KubeAuto Day Europe 2026 branding

## Slide 2: About Me / KodeKloud

- Brief intro
- KodeKloud: hands-on learning for DevOps and Cloud
- "I build things so other people can learn to build things"

## Slide 3: The Question

> "Does AI actually reduce platform engineering toil, or does it just
> convert 'writing YAML' into 'debugging AI YAML'?"

- Every vendor says AI will build your platform
- Nobody measures it honestly
- Today we fix that

## Slide 4: The Challenge

- Build a production-grade IDP on EKS
- 27 components across 7 phases
- AI does the implementation
- Human makes decisions and scores the results
- Everything documented, everything tested

## Slide 5: What We Built

Architecture diagram showing:
- EKS 1.34 + ArgoCD 3.3 (GitOps)
- Kyverno + Falco (Security)
- Prometheus + Grafana + OTel (Observability)
- ESO + Secrets Manager (Secrets)
- Backstage (Developer Portal)
- cert-manager, RBAC, NetworkPolicies, PDBs

## Slide 6: The Methodology

- Test-Driven Development (write test → implement → verify)
- No mocks — all tests hit live infrastructure
- Per-component scoring on 6 dimensions
- Honest recording of every correction cycle
- Open-source scorecard template

## Slide 7: The Scorecard Dimensions

1. **Toil Reduced** (1-10) — how much effort saved?
2. **Correction Cycles** — how many human interventions?
3. **AI Time** — wall-clock time to working component
4. **Manual Time** — estimated human-only time
5. **Toil Shifted?** — did toil move, or disappear?
6. **Notes** — what happened, honestly

## Slides 8-10: Live Demo (~5-7 min)

### Demo 1: GitOps in Action
- Show ArgoCD dashboard with 27 synced apps
- Make a change in Git → watch 30s reconciliation
- Show drift detection + self-healing

### Demo 2: Security Stack
- Trigger Kyverno policy (reject privileged pod)
- Trigger Falco alert (write to /etc in container)
- Show ESO secret sync from AWS Secrets Manager

### Demo 3: Developer Portal
- Open Backstage
- Show software catalog with sample app
- Walk through Backstage template for new service
- Show it produces Kyverno-compliant resources

## Slide 11: The Results — Headlines

| Metric | Value |
|--------|-------|
| AI build time | 3 hours 10 min |
| Manual estimate | 12 hours |
| Toil reduction | 73.8% |
| Correction cycles | 25 total |
| Zero-correction components | 48% |

## Slide 12: The Results — Detail

Full scorecard table (truncated for slide, full version in repo).
Highlight the color-coded pattern:
- Green (score 8-10): most components
- Yellow (score 6-7, partial shift): 5 components
- Red (score ≤ 3): zero components

## Slide 13: Where AI Helped Most

- Pattern-heavy boilerplate (ArgoCD apps, RBAC, NetworkPolicies)
- Documentation (SECURITY.md, ADRs, COST.md)
- Grafana dashboards + alert rules
- Anything with well-defined input/output

**Key insight:** AI excels at work that's tedious but not intellectually
challenging.

## Slide 14: Where AI Struggled

- **Version currency** — stale chart versions, deprecated APIs
- **Breaking changes** — module v20 → v21 variable renames
- **Helm chart internals** — template overrides vs values
- **Non-obvious interactions** — NetworkPolicy blocking test traffic

**Key insight:** AI fails at work that requires reading changelogs.

## Slide 15: The Toil Shift Problem

Show the 5 "Partial" components:
- EKS (module v21 renames)
- Kyverno (webhook config format)
- Falco (wrong chart version)
- ESO (API v1beta1 → v1)
- OTel (image breaking change)

Pattern: AI generated plausible-looking config with the wrong version of
something. Debugging "correct-looking but broken" is a different kind of
toil.

## Slide 16: Lessons Learned

1. **Skill files are essential** — give AI the right context
2. **Pin versions in prompts** — "install Falco 8.0.0", not "install Falco"
3. **TDD catches AI mistakes fast** — failing tests are instant feedback
4. **AI is best at boilerplate, worst at breaking changes**
5. **The scorecard is the real output** — build your own, share the results

## Slide 17: The Honest Take

> "73.8% toil reduction is real, but the remaining ~26% is harder toil.
> Debugging confident-but-wrong AI output is more cognitive load than
> writing config yourself."

- AI doesn't replace platform engineers
- AI makes experienced engineers faster
- AI is dangerous for juniors who can't spot wrong output
- Measure it. Don't trust vibes.

## Slide 18: Try It Yourself

- GitHub repo: `peopleforrester/kubeauto-ai-day`
- Scorecard template: `scorecard/SCORECARD-TEMPLATE.md`
- Full methodology: `scorecard/methodology.md`
- All ADRs: `docs/adr/`

QR code for repo link.

## Slide 19: Q&A

- Contact info
- KodeKloud links
- "Build your own scorecard. Share the results."

---

## Notes for Speaker

- Total talk time: ~30 min (including demo)
- Demo buffer: have screenshots as fallback if live demo fails
- Key talking points to emphasize:
  - This is about measurement, not advocacy
  - The scorecard template is the takeaway
  - "Toil shifted" is the nuanced finding
  - Version currency is AI's biggest weakness
