# Social Media Thread — KubeAuto Day Results

Published after KubeAuto Day Europe 2026 (March 23, Amsterdam).
Use this thread format for LinkedIn, Twitter/X, Bluesky, and Mastodon.

---

## Post 1/6 — The Hook

Two weeks ago I stood on stage at KubeAuto Day Europe and showed a
production-grade IDP I built with AI. Not a toy demo — EKS, ArgoCD,
Kyverno, Falco, Backstage, the full stack. 27 components. Test-driven.
Every correction cycle documented.

The honest scorecard:

AI build time: 3 hours 10 min
Manual estimate: 12 hours
Toil reduction: 73.8%

But the interesting part isn't the headline number. Thread below.

---

## Post 2/6 — What Worked

11 of 27 components (41%) had ZERO correction cycles. AI nailed them
first try:
- RBAC, NetworkPolicies, Kyverno policies
- Grafana dashboards, alert rules
- Backstage templates, documentation

Pattern: AI excels at well-defined, boilerplate-heavy work. If the inputs
and outputs are clear, AI is unbeatable.

---

## Post 3/6 — What Didn't

5 components had "toil shift" — AI converted writing toil into debugging
toil:
- Used Terraform module v20 patterns for v21
- Used Kyverno webhook config for the wrong chart version
- Used ESO API v1beta1 when v1 was required
- Used OTel k8s image when contrib was needed

Pattern: AI's #1 weakness is version currency. It generates confident,
correct-looking YAML that uses the wrong version of something.

---

## Post 4/6 — What Made the Difference

METR (2025) found developers believed AI made them +24% faster. They were
actually 19% slower. I measured 73.8% faster.

The difference isn't the AI. It's four constraints:

1. Skill files — pinned versions, known pitfalls, correct API shapes
2. TDD — failing test first = immediate signal when AI is wrong
3. Three-layer guardrails — git hooks, IDE hooks, Kubernetes admission
4. Human review — every output scored, every correction documented

Unconstrained AI wastes your time. Constrained AI saves it.

---

## Post 5/6 — Honest Caveats

Three things 73.8% doesn't tell you:

1. 60+ hours of invisible prep went in first (skill files, hooks,
   project config, studying context windows)
2. 30 years of experience caught the errors — AI makes senior engineers
   faster; it's risky for juniors who can't spot wrong output
3. This is 1 data point against METR's 16 — evidence, not proof

Every impressive number has a denominator. Now you know mine.

---

## Post 6/6 — Try It Yourself

Everything is open source. Run your own scorecard:

- Full repo: Terraform, ArgoCD apps, 59 tests, 9 ADRs
- Reusable scorecard template
- Scoring methodology
- Three-layer guardrail architecture

Build your own IDP. Score it honestly. Share the results.
The industry needs more data points, not more vendor demos.

github.com/peopleforrester/kubeauto-ai-day

#KubeAutoDay #PlatformEngineering #DevOps #InternalDeveloperPlatform #IDP #EKS #ArgoCD #CNCF
