# KubeAuto Day Europe 2026 — Attendee Reference

## Talk: "I Built an IDP with AI. Here's the Scorecard."

Speaker: Michael Forrester, KodeKloud

---

## Platform at a Glance

| Layer | Component | Version |
|-------|-----------|---------|
| Infrastructure | EKS on AWS | 1.34 |
| GitOps | ArgoCD | 3.2.6 |
| Policy | Kyverno | 1.17.0 |
| Runtime Security | Falco | 0.43.0 |
| Secrets | ESO + AWS Secrets Manager | 1.3.2 |
| Observability | Prometheus + Grafana + OTel | 3.9.1 / 12.3.3 / 0.145.0 |
| Developer Portal | Backstage | 1.9.1 |
| TLS | cert-manager | 1.19.3 |

## Repository

**GitHub**: github.com/peopleforrester/kubeauto-ai-day

The repo contains:
- Full Terraform configuration (`infrastructure/terraform/`)
- All ArgoCD Application manifests (`gitops/apps/`)
- Kyverno policies, Falco rules, NetworkPolicies (`security/`)
- Backstage catalog and templates (`backstage/`)
- Complete test suite (`tests/`)
- Architecture Decision Records (`docs/adr/`)
- The scorecard and methodology (`spec/SCORECARD.md`, `scorecard/`)

## Scorecard Highlights

| Metric | Value |
|--------|-------|
| AI build time | 3 hours |
| Manual estimate | 11.5 hours |
| Toil reduction | 73.6% |
| Components scored | 26/27 |
| Zero-correction rate | 50% |

## Use the Scorecard Template

Want to measure your own AI-assisted builds?

1. Copy `scorecard/SCORECARD-TEMPLATE.md` from the repo
2. Read `scorecard/methodology.md` for scoring definitions
3. Fill it in as you build — don't reconstruct after the fact
4. Share your results with the community

## Key Takeaways

1. **AI reduces toil by ~74% for IDP builds** — but the remaining 26% is harder
2. **Version currency is AI's #1 weakness** — always pin versions in prompts
3. **TDD catches AI mistakes immediately** — write the test first, always
4. **Skill files/context are essential** — generic prompts get generic (wrong) output
5. **Measure, don't guess** — vibes-based assessment of AI tools is unreliable

## Architecture Decision Records

| ADR | Decision |
|-----|----------|
| 001 | Terraform over Pulumi/CDK |
| 002 | ArgoCD over Flux |
| 003 | Kyverno over OPA/Gatekeeper |
| 003b | Falco for runtime security |
| 004 | ESO over Secrets Store CSI |
| 005 | Prometheus + Grafana over Datadog/Mimir |
| 006 | Backstage for developer portal |
| 007 | GitHub OIDC for authentication |

## Contact

- Michael Forrester — KodeKloud
- GitHub: peopleforrester
