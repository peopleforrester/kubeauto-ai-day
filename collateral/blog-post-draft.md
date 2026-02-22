# I Built an IDP with AI in 3 Hours. Here's What Actually Happened.

## The Promise

Every AI vendor will tell you their tool can build your infrastructure in
minutes. Every demo shows the happy path. Nobody talks about what happens
when the AI gets the Helm chart version wrong, uses a deprecated API, or
generates YAML that looks right but fails spectacularly at deploy time.

I wanted to find out: does AI-assisted platform building genuinely reduce
toil, or does it just convert "writing YAML" toil into "reviewing and
debugging AI YAML" toil?

## The Setup

I built a production-grade Internal Developer Platform on EKS from scratch,
with AI doing the heavy lifting. Every component was test-driven, every
decision recorded, and every correction cycle documented honestly.

**The platform:**
- EKS 1.34 on AWS (VPC, IAM, managed node groups)
- ArgoCD 3.3 for GitOps (app-of-apps pattern, 27 managed Applications)
- Kyverno 1.17 for policy enforcement (6 policies, enforce mode in apps namespace)
- Falco 0.43 for runtime security (eBPF driver, 5 custom rules)
- ESO for secret management (AWS Secrets Manager integration)
- Prometheus + Grafana + OTel for observability
- Backstage for developer portal (2 software templates)
- cert-manager for TLS
- ResourceQuotas, PDBs, RBAC, NetworkPolicies

**The methodology:**
- 27 planned components across 7 build phases
- Test-driven development: write failing test → implement → verify
- No mocks, no stubs — all tests hit live infrastructure
- Per-component scoring on a 6-dimension scorecard
- Honest recording of every correction cycle

**The AI tool:** Claude Code (Opus model) with project-specific skill files
providing component patterns and known pitfalls.

## The Results

| Metric | Value |
|--------|-------|
| Total AI-assisted build time | 3 hours 10 min |
| Estimated manual build time | 12 hours 5 min |
| Net toil reduction | 73.8% |
| Total correction cycles | 25 |
| Average quality score | 8.0/10 |
| Components with zero corrections | 13/27 (48%) |
| Components where AI shifted toil | 5/27 (19%) |
| Components where manual would be faster | 0/27 |

**The headline number: 73.8% toil reduction is real.** But the story behind
it is more nuanced than any vendor pitch will tell you.

## Where AI Genuinely Helped

**High-confidence, pattern-heavy work (score 9/10):**
Namespace definitions, RBAC manifests, NetworkPolicies, Kyverno policies,
Grafana dashboards, alert rules, PDBs, documentation. These are well-defined
patterns with clear inputs and outputs. AI produced correct output on the
first try in 13 of 26 components.

**Boilerplate reduction:**
ArgoCD Application manifests are 90% boilerplate. Once the AI understood the
app-of-apps pattern, it cranked out correct Application YAMLs instantly.
The human cost of manually writing 27 Application manifests is significant;
the AI cost was near zero.

**Documentation:**
SECURITY.md, COST.md, ADRs — AI produced comprehensive, well-structured
docs from context. This was the most unambiguous win. Writing docs manually
takes time because the writing itself is the bottleneck; AI removes that.

## Where AI Struggled

**Version currency (the #1 problem):**
The AI repeatedly used outdated versions. Falco chart 7.2.1 when 8.0.0 was
current. cert-manager v1.19.1 when v1.19.3 was available. ArgoCD skill file
referenced chart 7.x when 9.x was needed. Kyverno webhook config was wrong
for chart 3.7.0.

This is the most dangerous failure mode: the AI generates plausible-looking
config that uses an old API, and you don't notice until deployment fails.

**Breaking changes across major versions:**
The EKS Terraform module v21 renamed variables from v20. The AI's training
data included v20 patterns. Three correction cycles were spent on variable
renames that an engineer reading the v21 changelog would have caught
immediately.

**Stale macro/API references:**
Falco removed the `write_etc_common` macro in 0.42.x. ESO v1 uses `v1` API,
not `v1beta1`. OTel Collector chart 0.145 requires explicit `image.repository`
(breaking change from 0.89+). Each of these caused a correction cycle.

**Helm chart internals:**
The Falco chart's template computes the Falcosidekick URL as
`<release-name>-falcosidekick`. Setting the URL manually in values didn't
work because the template override. You had to use `falcosidekick.fullfqdn`.
AI doesn't read chart templates — it guesses from values files.

## The Five Components Where Toil Shifted

For 5 of 26 components, AI "partially shifted" toil rather than purely
reducing it:

1. **EKS Cluster** — Module v21 variable renames
2. **Kyverno Install** — Webhook config format wrong for chart version
3. **Falco Install** — Wrong chart version in skill file
4. **ESO** — API version v1beta1 → v1
5. **OTel Collector** — Breaking image change

The pattern: these are all cases where the AI's training data was stale.
It generated confident, syntactically-correct YAML that used the wrong
version of something. Debugging "why does this correct-looking config not
work" is a different kind of toil than writing config from scratch, but
it's still toil.

## Practical Advice for Teams

**1. Skill files are essential.**
The `.claude/skills/` files with component patterns, chart versions, and
known pitfalls were the single biggest factor in reducing correction cycles.
Without them, I estimate corrections would have doubled.

**2. Version-pin everything in your prompts.**
Don't say "install Falco." Say "install Falco chart 8.0.0 (Falco 0.43.0)
with modern_ebpf driver." The more specific your prompt, the fewer correction
cycles.

**3. TDD catches AI mistakes immediately.**
Writing the test first meant every wrong version, broken API, or misconfigured
value was caught within minutes, not hours. The AI fix-iterate cycle is fast
when you have a clear signal of what's wrong.

**4. AI is best at boilerplate and worst at breaking changes.**
If you're generating the 15th ArgoCD Application manifest, AI is unbeatable.
If you're using a chart version that changed its API between minor releases,
AI is a liability.

**5. The scorecard is the real output.**
The platform is a demo; the scorecard is the evidence. Run your own scorecard.
The template is in the repo.

## Try It Yourself

The full repository, scorecard, and methodology are open source:

- **Repository**: github.com/peopleforrester/kubeauto-ai-day
- **Scorecard Template**: `scorecard/SCORECARD-TEMPLATE.md`
- **Architecture**: `docs/ARCHITECTURE.md`
- **All ADRs**: `docs/adr/`

Build your own IDP. Score it honestly. Share the results. The industry needs
more data points, not more demos.

---

*Michael Forrester is a Platform Engineer at KodeKloud. This platform was
built for KubeAuto Day Europe 2026.*
