# AI Platform Building Scorecard

## Methodology

Each component is scored on six dimensions during the AI-assisted build.
Scores are updated per-component (not per-phase) as each component passes tests.

See `scorecard/methodology.md` (created in Phase 8) for full methodology.

## Scorecard

| Component | Toil Reduced (1-10) | Correction Cycles | AI Time | Est. Manual Time | Toil Shifted? | Notes |
|---|---|---|---|---|---|---|
| VPC + Networking | 7 | 1 | 5 min | 30 min | No | VPC module config straightforward; NAT gateway + subnet tagging correct first try |
| EKS Cluster | 6 | 3 | 25 min | 45 min | Partial | Module v21.15 variable renames caused 2 correction cycles; AWS provider 6.x dependency; addon bootstrap chicken-and-egg required manual intervention |
| IAM Roles + Pod Identity | 7 | 1 | 5 min | 25 min | No | IRSA roles for EBS CSI + LB Controller correct; Helm release for LB Controller wired properly |
| Namespace Structure | 9 | 0 | 2 min | 10 min | No | PSS labels on apps namespace correct first try; clean YAML |
| ArgoCD Install + Config | | | | | | |
| App-of-Apps Pattern | | | | | | |
| Sync Waves + Ordering | | | | | | |
| Kyverno Install | | | | | | |
| Kyverno Policies (individual) | | | | | | |
| Kyverno Policy Interactions | | | | | | |
| Falco Install | | | | | | |
| Falco Custom Rules | | | | | | |
| ESO + Secrets Manager | | | | | | |
| RBAC | | | | | | |
| NetworkPolicies | | | | | | |
| Prometheus + Grafana | | | | | | |
| OTel Collector Config | | | | | | |
| Grafana Dashboards | | | | | | |
| Alert Rules | | | | | | |
| Backstage Install | | | | | | |
| Software Templates | | | | | | |
| Backstage Plugin Wiring | | | | | | |
| E2E Integration | | | | | | |
| TLS + cert-manager | | | | | | |
| OIDC Authentication | | | | | | |
| Documentation | | | | | | |
| Architecture Decision Records | | | | | | |

## Totals

- Total AI-assisted build time: ___ hours
- Total human correction time: ___ hours
- Estimated manual build time: ___ hours
- Net toil reduction: ___%
- Components where AI genuinely reduced toil: ___/27
- Components where AI shifted toil without reducing it: ___/27
- Components where starting from scratch would have been faster: ___/27

## Scoring Key

**Toil Reduced (1-10):**
- 10 = Would have taken hours manually, AI did it in minutes with no corrections
- 5 = AI produced a starting point, but required significant human correction
- 1 = AI output was wrong enough that starting from scratch would have been faster

**Correction Cycles:** Number of times AI output needed human intervention.

**Toil Shifted?:**
- Yes = AI converted "writing YAML" toil into "reviewing and debugging AI YAML" toil
- No = AI genuinely reduced total effort
- Partial = Some reduction, some shift
