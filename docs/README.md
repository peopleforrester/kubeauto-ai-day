# Documentation

## Reading Guide

Start here and work through in order:

| # | Document | What You'll Learn |
|---|----------|-------------------|
| 1 | [SETUP.md](SETUP.md) | How to reproduce the platform from scratch |
| 2 | [ARCHITECTURE.md](ARCHITECTURE.md) | Platform architecture, component relationships, data flows |
| 3 | [WALKTHROUGH.md](WALKTHROUGH.md) | Complete build narrative with Three-Layer Guardrail Architecture |
| 4 | [SECURITY.md](SECURITY.md) | Security posture: Kyverno, Falco, RBAC, ESO, NetworkPolicies |
| 5 | [EIGHT-GUARDRAILS.md](EIGHT-GUARDRAILS.md) | Eight Guardrails framework reference |

## Reference Documents

| Document | Purpose |
|----------|---------|
| [COST.md](COST.md) | AWS cost breakdown (~$0.57/hr) |
| [TEARDOWN.md](TEARDOWN.md) | How to destroy the cluster and clean up AWS resources |
| [VERSION-MAP.md](VERSION-MAP.md) | Every component version pinned in the platform |
| [LESSONS-LEARNED.md](LESSONS-LEARNED.md) | What went wrong and what we'd do differently |
| [EIGHT-GUARDRAILS-RECONCILIATION.md](EIGHT-GUARDRAILS-RECONCILIATION.md) | Gap analysis of guardrail implementation |

## Architecture Decision Records

9 ADRs in [adr/](adr/):

| ADR | Decision |
|-----|----------|
| [000](adr/ADR-000-domain-name.md) | Domain name |
| [001](adr/ADR-001-iac-tool.md) | Terraform |
| [002](adr/ADR-002-gitops-engine.md) | ArgoCD |
| [003](adr/ADR-003-policy-engine.md) | Kyverno |
| [003b](adr/ADR-003b-runtime-security.md) | Falco |
| [004](adr/ADR-004-secret-management.md) | ESO |
| [005](adr/ADR-005-observability-stack.md) | Prometheus + Grafana |
| [006](adr/ADR-006-developer-portal.md) | Backstage |
| [007](adr/ADR-007-auth-strategy.md) | GitHub OIDC |

## Local-Only Documents

These files exist locally but are gitignored (build planning, not reference):
- `spec.md` — Full build specification
- `PRD.md` — Product requirements document
- `PLAN.md` — Step-by-step execution plan
