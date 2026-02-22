# KubeAuto Day IDP — AI Platform Building Scorecard

A production-grade Internal Developer Platform on EKS, built with AI assistance
and measured honestly.

## What This Is

This repository contains a complete IDP built for
[KubeAuto Day Europe 2026](https://events.linuxfoundation.org/kubecon-cloudnativecon-europe/co-located-events/kubeauto-ai-day/).
Every component was built using AI-assisted development (Claude Code) with
test-driven methodology. Every correction cycle was documented.

The platform is real. The scorecard is honest. The methodology is reusable.

## The Scorecard

| Metric | Value |
|--------|-------|
| AI build time | 3 hours 10 min |
| Manual estimate | 12 hours |
| Toil reduction | 73.8% |
| Components scored | 27/27 |
| Zero-correction rate | 48% |
| Average quality score | 8.0/10 |

Full scorecard: [`spec/SCORECARD.md`](spec/SCORECARD.md)

## Deep Dives

- [**Architecture**](docs/ARCHITECTURE.md) — Platform architecture, component relationships, data flows
- [**Walkthrough**](docs/WALKTHROUGH.md) — Complete build narrative with Three-Layer Guardrail Architecture
- [**Eight Guardrails**](docs/EIGHT-GUARDRAILS.md) — Defense-in-depth framework (Git → Claude Code → Kubernetes)
- [**Security**](docs/SECURITY.md) — Kyverno, Falco, RBAC, ESO, NetworkPolicies, cert-manager
- [**Lessons Learned**](docs/LESSONS-LEARNED.md) — What went wrong and what we'd do differently

## Platform Stack

| Layer | Component | Version |
|-------|-----------|---------|
| Infrastructure | EKS on AWS | 1.34 |
| GitOps | ArgoCD | 3.3.0 |
| Policy Enforcement | Kyverno | 1.17.0 |
| Runtime Security | Falco (eBPF) | 0.43.0 |
| Secret Management | ESO + AWS Secrets Manager | 1.3.2 |
| Observability | Prometheus + Grafana + OTel | 3.9.1 / 12.3.3 / 0.145.0 |
| Developer Portal | Backstage | 1.9.1 |
| TLS | cert-manager + Let's Encrypt | 1.19.3 |

27 ArgoCD Applications managed via app-of-apps pattern.

## Repository Structure

```
infrastructure/terraform/   # EKS, VPC, IAM (Terraform)
gitops/
  bootstrap/                # ArgoCD + root app-of-apps
  apps/                     # 26 ArgoCD Application manifests
  namespaces/               # Namespace definitions
security/
  kyverno/                  # 6 ClusterPolicies
  falco/                    # 5 custom Falco rules
  eso/                      # ClusterSecretStore + ExternalSecrets
  rbac/                     # ClusterRoles + RoleBindings
  network-policies/         # Default-deny + allow rules
  cert-manager/             # ClusterIssuers
  quotas-pdbs/              # ResourceQuota + 5 PDBs
observability/
  grafana/dashboards/       # Grafana Platform Overview dashboard
backstage/
  catalog/                  # System, Component, Templates
  templates/                # deploy-service, create-namespace
sample-app/                 # Python Flask app with OTel
tests/                      # 59 tests across 7 phases (real infra, no mocks)
docs/
  adr/                      # 9 Architecture Decision Records
  ARCHITECTURE.md           # Platform architecture overview
  SETUP.md                  # Reproduction guide
  TEARDOWN.md               # Cluster destruction guide
  SECURITY.md               # Security posture summary
  COST.md                   # AWS cost breakdown
scorecard/
  methodology.md            # Scoring definitions
  raw-scores.json           # Machine-readable results
  SCORECARD-TEMPLATE.md     # Blank template for your own builds
collateral/
  demo-runbook.md           # Live demo commands
  blog-post-draft.md        # Conference blog post
  slide-outline.md          # Talk slide structure
  attendee-handout.md       # Audience reference card
  social-media-thread.md    # Announcement thread
```

## Use the Scorecard Template

Want to measure your own AI-assisted builds?

1. Copy [`scorecard/SCORECARD-TEMPLATE.md`](scorecard/SCORECARD-TEMPLATE.md)
2. Read [`scorecard/methodology.md`](scorecard/methodology.md) for scoring definitions
3. Fill it in as you build (don't reconstruct after the fact)
4. Share your results

## Reproduce the Platform

See [`docs/SETUP.md`](docs/SETUP.md) for step-by-step instructions.

**Prerequisites:** AWS account, Terraform >= 1.7, kubectl, Helm, Python 3.12+, uv.

**Cost:** ~$0.57/hr while running. See [`docs/COST.md`](docs/COST.md).

**Teardown:** See [`docs/TEARDOWN.md`](docs/TEARDOWN.md).

## Architecture Decisions

| ADR | Decision |
|-----|----------|
| [000](docs/adr/ADR-000-domain-name.md) | Domain name (ai-enhanced-devops.com) |
| [001](docs/adr/ADR-001-iac-tool.md) | Terraform over Pulumi/CDK |
| [002](docs/adr/ADR-002-gitops-engine.md) | ArgoCD over Flux |
| [003](docs/adr/ADR-003-policy-engine.md) | Kyverno over OPA/Gatekeeper |
| [003b](docs/adr/ADR-003b-runtime-security.md) | Falco for runtime security |
| [004](docs/adr/ADR-004-secret-management.md) | ESO over Secrets Store CSI |
| [005](docs/adr/ADR-005-observability-stack.md) | Prometheus + Grafana over Datadog/Mimir |
| [006](docs/adr/ADR-006-developer-portal.md) | Backstage for developer portal |
| [007](docs/adr/ADR-007-auth-strategy.md) | GitHub OIDC for authentication |

## Key Findings

1. **AI reduces IDP build toil by ~74%** — but the remaining 26% is harder toil
2. **48% of components had zero corrections** — AI excels at boilerplate
3. **Version currency is AI's #1 weakness** — stale chart versions, deprecated APIs
4. **TDD catches AI mistakes fast** — write the test first, always
5. **Skill files/context are essential** — generic prompts get generic errors

## License

Apache 2.0. See [LICENSE](LICENSE).

## Author

Michael Forrester — [KodeKloud](https://kodekloud.com)

Built for KubeAuto Day Europe 2026, London.
