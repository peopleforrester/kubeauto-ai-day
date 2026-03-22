# Social Media Thread — KubeAuto Day Results

Use this thread format for LinkedIn, Twitter/X, and Mastodon.

---

## Post 1/5 — The Hook

I built a production-grade IDP with AI. Not a toy demo — EKS, ArgoCD, Kyverno,
Falco, Backstage, the full stack. 27 components. Test-driven. Every correction
cycle documented.

Here's the honest scorecard:

AI build time: 3 hours 10 min
Manual estimate: 12 hours
Toil reduction: 73.8%

But the interesting part isn't the headline number.

---

## Post 2/5 — What Worked

11 of 27 components (41%) had ZERO correction cycles. AI nailed them
first try:
- RBAC, NetworkPolicies, Kyverno policies
- Grafana dashboards, alert rules
- Backstage templates, documentation

Pattern: AI excels at well-defined, boilerplate-heavy work. If the inputs and
outputs are clear, AI is unbeatable.

---

## Post 3/5 — What Didn't

5 components had "toil shift" — AI converted writing toil into debugging toil:
- Used Falco chart 7.2.1 when 8.0.0 was current
- Used Terraform module v20 patterns for v21
- Used ESO API v1beta1 when v1 was required
- Used OTel k8s image when contrib was needed

Pattern: AI's #1 weakness is version currency. It generates confident,
correct-looking YAML that uses the wrong version of something.

---

## Post 4/5 — The Takeaways

For platform teams considering AI:

1. Pin versions in your prompts (not "install Falco" but "install Falco 8.0.0")
2. Write tests first — they catch AI mistakes in minutes, not hours
3. Give AI context (skill files, known pitfalls) — generic prompts get generic errors
4. AI makes experienced engineers faster; it's risky for juniors who can't spot wrong output
5. Measure it. Don't trust vibes.

---

## Post 5/5 — Try It Yourself

Everything is open source:

- Full repo with Terraform, ArgoCD apps, tests
- Reusable scorecard template
- Scoring methodology
- 9 Architecture Decision Records

Build your own IDP. Score it honestly. Share the results.

The industry needs more data points, not more vendor demos.

Link: github.com/peopleforrester/kubeauto-ai-day

#KubeAutoDay #KubeAuto #PlatformEngineering #DevOps #AI #IDP #EKS
